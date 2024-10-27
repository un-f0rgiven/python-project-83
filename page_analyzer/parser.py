from bs4 import BeautifulSoup


def parse_html(html):
    soup = BeautifulSoup(html, 'html.parser')

    h1_content = soup.find('h1').get_text() if soup.find('h1') else ''
    title_content = soup.title.string if soup.title else ''
    description_content = soup.find('meta', attrs={'name': 'description'})
    description_content = (
        description_content['content'] if description_content else ''
    )

    return h1_content, title_content, description_content
