from flask import Flask, flash, get_flashed_messages, redirect, \
    render_template, request, session, url_for
from dotenv import load_dotenv
from urllib.parse import urlparse
from validators.url import url
import os
import psycopg2

load_dotenv()

app = Flask(__name__)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

DATABASE_URL = os.getenv('DATABASE_URL')
conn = psycopg2.connect(DATABASE_URL)


class DB:
    def __init__(self, database_url, table, table_descr):
        self.database_url = database_url
        self.table = table
        self.table_descr = table_descr

    def _read_db(
        self,
        filds='*',
        search_fild='',
        search_value='',
        reverse=False
    ):
        table = self.table
        query = f"SELECT {filds} FROM {table}"
        if search_fild:
            query += f' WHERE {search_fild} = %s'
        if reverse:
            query += ' ORDER BY id DESC'
        if isinstance(search_value, int):
            search_value = str(search_value)
        try:
            with psycopg2.connect(self.database_url) as conn:
                with conn.cursor() as cur:
                    if search_fild:
                        print('СМОТРИ СЮДА', query, search_value)
                        cur.execute(query, (search_value,))
                    else:
                        print('СМОТРИ СЮДА', query)
                        cur.execute(query)
                    result = cur.fetchall()
                    return result
        except (psycopg2.Error, Exception) as error:
            # Обработка ошибок, например, вывод сообщения или логирование
            print("Error reading data from the database:", error)
            return None

    def _write_db(self, value):
        table = f'{self.table} ({", ".join(self.table_descr)})'
        query = f"INSERT INTO {table} VALUES (%s)"
        try:
            with psycopg2.connect(self.database_url) as conn:
                with conn.cursor() as cur:
                    cur.execute(query, value)
                    conn.commit()
        except (psycopg2.Error, Exception) as error:
            # Обработка ошибок, например, вывод сообщения или логирование
            print("Error write data in the database:", error)

    def content(self, reverse=False):
        return self._read_db(reverse=reverse)

    def find(self, fild, value):
        return self._read_db(search_fild=fild, search_value=value)

    def insert(self, value):
        value = (value,)
        self._write_db(value)


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

    repo = DB(DATABASE_URL, 'urls', ('name',))
    table = repo.content(reverse=True)

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
    id = repo.find('name', normalize_url)[0][0]

    flash('Страница успешно добавлена', 'success')
    return redirect(url_for('urls_id_get', id=id), code=302)


@app.route('/urls/<int:id>')
def urls_id_get(id):
    messages = get_flashed_messages(with_categories=True)

    repo = DB(DATABASE_URL, 'urls', ('name',))
    entry = repo.find('id', id)[0]

    return render_template(
        'url.html',
        messages=messages,
        entry=entry
    )
