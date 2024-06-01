from dotenv import load_dotenv
from page_analyzer.constants import URLS_QUERY
from page_analyzer.db_manager import TableManagerWithConstructor, \
    TableManager
from page_analyzer.parser import get_site_info
from urllib.parse import urlparse
from validators.url import url
import os
import requests

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')


def normalize(raw_url: str) -> str:
    url_tup = urlparse(raw_url)
    normalize_url = f'{url_tup.scheme}://{url_tup.hostname}'
    return normalize_url


def validate(normalize_url: str) -> bool:
    return url(normalize_url) is True and len(normalize_url) < 256


def get_urls_check_table() -> list:
    repo = TableManager(DATABASE_URL, 'urls', ('name',))
    table = repo.get(query=URLS_QUERY)
    return table


def add_value_in_urls(raw_url: str) -> tuple:
    normalized_url = normalize(raw_url)

    if not validate(normalized_url):
        return None, 'danger'

    repo = TableManagerWithConstructor(DATABASE_URL, 'urls', ('name',))

    try:
        repo.insert(normalized_url)
        message = 'success'
    except Exception as error:
        if 'duplicate' in str(error):
            message = 'info'

    id = repo.get_one('name', normalized_url, fields='id')[0]
    return id, message


def get_value_from_urls(search_value) -> tuple:
    search_field = 'id'
    repo = TableManagerWithConstructor(DATABASE_URL, 'urls', ('name',))
    return repo.get_one(search_field, search_value, fields='*')


def get_value_from_url_checks(search_value) -> list:
    search_field = 'url_id'
    repo = TableManagerWithConstructor(DATABASE_URL, 'url_checks', ('url_id',))
    return repo.get_many(search_field, search_value, fields='*', reverse=True)


def check_url(id: int) -> str:
    repo = TableManagerWithConstructor(DATABASE_URL, 'urls', ('name',))
    url = repo.get_one(search_field='id', search_value=id, fields='name')[0]

    try:
        html_doc = requests.get(url, timeout=15)
    except (ConnectionError, Exception) as error:
        print("Error check url:", error)
        return 'danger'

    status_code = html_doc.status_code
    if status_code != 200:
        return 'danger'

    site_info = get_site_info(html_doc)

    repo = TableManagerWithConstructor(
        DATABASE_URL,
        'url_checks',
        ('url_id', 'status_code', 'h1', 'title', 'description')
    )
    repo.insert(id, status_code, *site_info)
    return 'success'


def get_text_from_file(path):
    with open(path) as file:
        ascii_art = file.read()
    return ascii_art
