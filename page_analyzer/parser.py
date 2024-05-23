from bs4 import BeautifulSoup


def get_site_info(html_doc):
    soup = BeautifulSoup(html_doc.text, 'html.parser')

    h1 = soup.h1.text if soup.h1 else ''

    title = soup.title.string if soup.title else ''

    raw_description = soup.find(attrs={"name": "description"})
    description = raw_description['content']\
        if 'content' in str(raw_description) else ''

    return h1, title, description
