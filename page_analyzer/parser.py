from bs4 import BeautifulSoup


def get_site_info(html_doc):
    soup = BeautifulSoup(html_doc.text, 'html.parser')

    h1 = soup.h1.text if soup.h1 else ''

    title = soup.title.string if soup.title else ''

    raw_description = soup.find(attrs={"name": "description"})
    description = raw_description['content']\
        if 'content' in str(raw_description) else ''

    return h1, title, description

# alt


class Parser:
    def __init__(self, html_doc):
        self.soup = BeautifulSoup(html_doc.text, 'html.parser')

    def get_h1(self):
        if self.soup.h1:
            return self.soup.h1.text
        return ''

    def get_title(self):
        if self.soup.title:
            return self.soup.title.string
        return ''

    def get_description(self):
        raw_description = self.soup.find(attrs={"name": "description"})
        if 'content' in str(raw_description):
            return raw_description['content']
        return ''

    def get_site_info(self):
        return self.get_h1, self.get_title, self.get_description
