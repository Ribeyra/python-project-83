from bs4 import BeautifulSoup
from flask import Flask, flash, get_flashed_messages, redirect, \
    render_template, request, session, url_for
from dotenv import load_dotenv
from urllib.parse import urlparse
from validators.url import url
import os
import psycopg2
import requests

load_dotenv()

app = Flask(__name__)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

DATABASE_URL = os.getenv('DATABASE_URL')
conn = psycopg2.connect(DATABASE_URL)

URLS_QUERY = """SELECT
    urls.id AS id,
    urls.name AS name,
    lc.last_check AS last_check,
    lc.status_code AS status_code
FROM urls
LEFT JOIN (
    SELECT
        uc.url_id,
        uc.status_code,
        uc.created_at AS last_check
    FROM
        url_checks uc
    JOIN (
        SELECT
            url_id,
            MAX(id) AS max_id
        FROM
            url_checks
        GROUP BY
            url_id
    ) AS latest_checks
    ON
        uc.id = latest_checks.max_id
) AS lc ON urls.id = lc.url_id
ORDER BY id DESC;
"""


class DB:
    def __init__(self, database_url, table, table_descr):
        self.database_url = database_url
        self.table = table
        self.table_descr = table_descr

    def _query_constructor(
        self,
        *,
        fields='*',
        search_field='',
        reverse=False,
        **kwargs
    ) -> str:

        query_templates = {
            'select': f'SELECT {fields} FROM {self.table}',
            'where': f'WHERE {search_field} = %s' if search_field else '',
            'reverse': 'ORDER BY id DESC' if reverse else ''
        }

        query_list = [value for value in query_templates.values() if value]

        query = ' '.join(query_list)
        return query

    def _read_db(self, *args, one=False, **kwargs):

        query = self._query_constructor(**kwargs)
        search_value = kwargs.get('search_value')

        try:
            with psycopg2.connect(self.database_url) as conn:
                with conn.cursor() as cur:
                    if search_value:
                        cur.execute(query, (search_value,))
                    else:
                        cur.execute(query)
                    result = cur.fetchone() if one else cur.fetchall()
                    return result
        except (psycopg2.Error, Exception) as error:
            print("Error reading data from the database:", error)
            return None

    def _write_db(self, value):

        table = f'{self.table} ({", ".join(self.table_descr)})'
        query = f"INSERT INTO {table} VALUES %s"

        try:
            with psycopg2.connect(self.database_url) as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (value,))
                    conn.commit()
        except (psycopg2.Error, Exception) as error:
            print("Error write data in the database:", error)

    def content(self, **kwargs):
        return self._read_db(**kwargs)

    def find(self, search_field, search_value, **kwargs):
        return self._read_db(
            search_field=search_field,
            search_value=search_value,
            **kwargs
        )

    def insert(self, *value):
        print(value)
        self._write_db(value)


class ComplexQuery(DB):
    def _query_constructor(*args, **kwargs):
        return kwargs['query']


def normalize(raw_url):
    url_tup = urlparse(raw_url)
    normalize_url = f'{url_tup.scheme}://{url_tup.hostname}'
    return normalize_url


def validate(normalize_url):
    return url(normalize_url) is True and len(normalize_url) < 256


@app.route('/')
def index():
    messages = get_flashed_messages(with_categories=True)

    return render_template(
        'index.html',
        messages=messages
    )


@app.get('/urls')
def urls_get():
    messages = get_flashed_messages(with_categories=True)

    if messages:
        wrong_url = session.pop('wrong_url', '')
        return render_template(
            'index.html',
            messages=messages,
            url=wrong_url
        ), 422

    repo = ComplexQuery(DATABASE_URL, 'urls', ('name',))
    table = repo.content(query=URLS_QUERY)

    return render_template(
        'urls.html',
        messages=messages,
        table=table
    )


@app.post('/urls')
def urls_post():
    raw_url = request.form.to_dict()['url']
    normalize_url = normalize(raw_url)

    if not validate(normalize_url):
        flash('Некорректный URL', 'error')
        session['wrong_url'] = raw_url
        return redirect(url_for('urls_get'), code=302)

    repo = DB(DATABASE_URL, 'urls', ('name',))
    repo.insert(normalize_url)
    id = repo.find('name', normalize_url, one=True)[0]

    flash('Страница успешно добавлена', 'success')
    return redirect(url_for('urls_id_get', id=id), code=302)


@app.route('/urls/<int:id>')
def urls_id_get(id):
    messages = get_flashed_messages(with_categories=True)

    repo_urls = DB(DATABASE_URL, 'urls', ('name',))
    entry = repo_urls.find('id', id, one=True)

    repo_urls = DB(DATABASE_URL, 'url_checks', ('url_id',))
    checks = repo_urls.find('url_id', id, reverse=True)

    return render_template(
        'url.html',
        messages=messages,
        entry=entry,
        checks=checks
    )


@app.post('/urls/<int:id>/checks')
def checks_post(id):

    repo = DB(DATABASE_URL, 'urls', ('name',))
    url = repo.find('id', id, fields='name', one=True)[0]

    try:
        check_url = requests.get(url, timeout=15)
    except (ConnectionError, Exception) as error:
        print("Error check url:", error)
        flash('Произошла ошибка при проверке', 'error')
        return redirect(url_for('urls_id_get', id=id), code=302)

    status_code = check_url.status_code

    soup = BeautifulSoup(check_url.text, 'html.parser')
    h1 = soup.h1.string if soup.h1 else ''
    title = soup.title.string if soup.title else ''
    description = soup.find(
        attrs={"name": "description"}
    )['content'] if soup.meta else ''

    repo = DB(
        DATABASE_URL,
        'url_checks',
        ('url_id', 'status_code', 'h1', 'title', 'description')
    )
    repo.insert(id, status_code, h1, title, description)

    flash('Страница успешно проверена', 'success')
    return redirect(url_for('urls_id_get', id=id), code=302)
