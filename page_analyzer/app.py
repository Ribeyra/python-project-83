from dotenv import load_dotenv
from flask import Flask, abort, flash, get_flashed_messages, redirect, \
    render_template, request, url_for
from page_analyzer.model import add_value_in_urls, check_url, \
    get_text_from_file, get_value_from_urls, get_value_from_url_checks, \
    get_urls_check_table
import os

load_dotenv()

app = Flask(__name__)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')


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
    table = get_urls_check_table()
    return render_template(
        'urls.html',
        messages=messages,
        table=table
    )


@app.post('/urls')
def urls_post():
    message_dict = {
        'info': ('Страница уже существует', 'info'),
        'success': ('Страница успешно добавлена', 'success')
    }

    raw_url = request.form.get('url')
    id, message = add_value_in_urls(raw_url)

    if message == 'danger':
        messages = [('danger', 'Некорректный URL')]
        return render_template(
            'index.html',
            messages=messages,
            url=raw_url
        ), 422

    flash(*message_dict[message])
    return redirect(url_for('urls_id_get', id=id), code=302)


@app.route('/urls/<int:id>')
def urls_id_get(id):
    messages = get_flashed_messages(with_categories=True)
    entry = get_value_from_urls(id)

    if entry is None:
        abort(404)

    checks = get_value_from_url_checks(id)

    return render_template(
        'url.html',
        messages=messages,
        entry=entry,
        checks=checks
    )


@app.post('/urls/<int:id>/checks')
def checks_post(id):
    message_dict = {
        'danger': ('Произошла ошибка при проверке', 'danger'),
        'success': ('Страница успешно проверена', 'success')
    }

    message = check_url(id)

    flash(*message_dict[message])
    return redirect(url_for('urls_id_get', id=id), code=302)


@app.route('/error')
def error():
    raise


@app.errorhandler(404)
def page_not_found(e):
    ascii_art = get_text_from_file('assets/not_that_droids.txt')
    return render_template('404.html', ascii_art=ascii_art), 404


@app.errorhandler(500)
def internal_server_error(e):
    ascii_art = get_text_from_file('assets/honest_work.txt')
    return render_template('500.html', ascii_art=ascii_art), 500
