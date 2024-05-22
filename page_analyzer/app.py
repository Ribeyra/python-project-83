from bs4 import BeautifulSoup
from dotenv import load_dotenv
from flask import Flask, abort, flash, get_flashed_messages, redirect, \
    render_template, request, url_for
from page_analyzer.constants import URLS_QUERY
from page_analyzer.db_manager import DatabaseManager, DBManagerForComplexQuery
from urllib.parse import urlparse
from validators.url import url
import os
import requests

load_dotenv()

app = Flask(__name__)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

DATABASE_URL = os.getenv('DATABASE_URL')


def normalize(raw_url: str) -> str:
    url_tup = urlparse(raw_url)
    normalize_url = f'{url_tup.scheme}://{url_tup.hostname}'
    return normalize_url


def validate(normalize_url: str) -> bool:
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

    repo = DBManagerForComplexQuery(DATABASE_URL, 'urls', ('name',))
    table = repo.content(query=URLS_QUERY)

    return render_template(
        'urls.html',
        messages=messages,
        table=table
    )


@app.post('/urls')
def urls_post():
    raw_url = request.form.get('url')
    normalized_url = normalize(raw_url)

    if not validate(normalized_url):
        messages = [('danger', 'Некорректный URL')]
        return render_template(
            'index.html',
            messages=messages,
            url=raw_url
        ), 422

    repo = DatabaseManager(DATABASE_URL, 'urls', ('name',))
    try:
        repo.insert(normalized_url)
        flash('Страница успешно добавлена', 'success')
    except Exception as error:
        if 'duplicate' in str(error):
            flash('Страница уже существует', 'info')

    id = repo.find('name', normalized_url, one=True, fields='id')[0]

    return redirect(url_for('urls_id_get', id=id), code=302)


@app.route('/urls/<int:id>')
def urls_id_get(id):
    messages = get_flashed_messages(with_categories=True)

    repo_urls = DatabaseManager(DATABASE_URL, 'urls', ('name',))
    entry = repo_urls.find('id', id, one=True)

    if entry is None:
        abort(404)

    repo_urls = DatabaseManager(DATABASE_URL, 'url_checks', ('url_id',))
    checks = repo_urls.find('url_id', id, reverse=True)

    return render_template(
        'url.html',
        messages=messages,
        entry=entry,
        checks=checks
    )


@app.post('/urls/<int:id>/checks')
def checks_post(id):

    repo = DatabaseManager(DATABASE_URL, 'urls', ('name',))
    url = repo.find('id', id, fields='name', one=True)[0]

    try:
        check_url = requests.get(url, timeout=15)
    except (ConnectionError, Exception) as error:
        print("Error check url:", error)
        flash('Произошла ошибка при проверке', 'danger')
        return redirect(url_for('urls_id_get', id=id), code=302)

    status_code = check_url.status_code
    if status_code != 200:
        flash('Произошла ошибка при проверке', 'danger')
        return redirect(url_for('urls_id_get', id=id), code=302)

    soup = BeautifulSoup(check_url.text, 'html.parser')
    h1 = soup.h1.string if soup.h1 else ''
    title = soup.title.string if soup.title else ''
    raw_description = soup.find(attrs={"name": "description"})
    description = raw_description['content']\
        if 'content' in str(raw_description) else ''

    repo = DatabaseManager(
        DATABASE_URL,
        'url_checks',
        ('url_id', 'status_code', 'h1', 'title', 'description')
    )
    repo.insert(id, status_code, h1, title, description)

    flash('Страница успешно проверена', 'success')
    return redirect(url_for('urls_id_get', id=id), code=302)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404
