from requests import Session
import requests
from bs4 import BeautifulSoup
from time import sleep, strptime
from io import BytesIO


class GoogleNewsURLDumper:
    def _get_data(self, request_text):
        soup = BeautifulSoup(request_text, 'lxml')
        data = soup.find_all('div', class_='ts')
        if not data:
            yield None
        for ts in data:
            url = ts.find('a')['href']
            yield url

    def _check_search_string(self):
        req = requests.get(self.url, params=self.params, headers=self.headers)
        print(req.text)
        for x in self._get_data(req.text):
            if not x:
                return False
        return True

    def __init__(self, search_string, after=None, before=None):
        self.url = 'https://www.google.ru/search'
        self.params = {
            'q': '{} {} {}'.format(
                search_string,
                (lambda after: '' if not after else 'after:{}'.format(after))(after),
                (lambda before: '' if not before else 'before:{}'.format(before))(before)
            ),
            'source': 'lnms',
            'tbm': 'nws',
            'start': 0,
            'newwindow': 1
        }
        self.headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
                          'Chrome/70.0.3538.77 Safari/537.36'
        }
        if not self._check_search_string():
            raise ValueError('Wrong search string')

    def dump(self):
        with Session() as s:
            data = ''
            flag = True
            while flag:
                req_text = s.get(self.url, params=self.params, headers=self.headers).text
                print(req_text)
                for url in self._get_data(req_text):
                    if not url:
                        flag = False
                        break
                    data += '{}\n'.format(url)
                self.params['start'] += 10
                sleep(1)
            return BytesIO(data.encode())


def check_date(date):
    try:
        strptime(date, '%Y-%m-%d')
        return True
    except ValueError:
        return False
