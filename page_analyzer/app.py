from flask import Flask, flash, get_flashed_messages, redirect, \
    render_template, request, url_for
from dotenv import load_dotenv
from urllib.parse import urlparse
from validators.url import url
import os
import psycopg2     # noqa f401

app = Flask(__name__)

load_dotenv()
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

# DATABASE_URL = os.getenv('DATABASE_URL')
# conn = psycopg2.connect(DATABASE_URL)


def normalize(raw_url):
    url_tup = urlparse(raw_url)
    normalize_url = f'{url_tup.scheme}://{url_tup.hostname}'
    return normalize_url


def validate(normalize_url):
    return url(normalize_url)


@app.route('/')
def index():

    messages = get_flashed_messages(with_categories=True)
    return render_template(
        'index.html',
        messages=messages,
        url=''
    )


@app.post('/urls')
def urls():
    messages = get_flashed_messages(with_categories=True)

    raw_url = request.form.to_dict()['url']
    normalize_url = normalize(raw_url)

    if validate(normalize_url) is not True:
        flash('url не прошел валидацию', 'error')
        return render_template(
            'index.html',
            messages=messages,
            url=raw_url
        )

    flash('url прошел валидацию', 'success')
    return redirect(url_for('index'), code=302)
