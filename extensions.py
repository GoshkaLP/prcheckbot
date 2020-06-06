import requests
from requests import Session
from bs4 import BeautifulSoup
from time import sleep, strptime
from io import BytesIO


class GoogleNewsURLDumper:
    def _get_data(self, request_text):
        soup = BeautifulSoup(request_text, 'lxml')
        data = soup.find_all('div', class_='ts')
        if not data:
            yield None
        for elem in data:
            url = elem.find('a', href=True)['href']
            yield url

    def _check_search_string(self):
        req = requests.get(self.url, params=self.params, headers=self.headers)
        print(req.text)
        if req.status_code == '429':
            raise ValueError('Too many requests')
        for x in self._get_data(req.text):
            if not x:
                return False
            else:
                break
        return True

    def __init__(self, search_string, after=None, before=None):
        self.url = 'https://www.google.ru/search'
        self.params = {
            'q': '{} {} {}'.format(
                search_string,
                (lambda after: '' if not after else 'after:{}'.format(after))(after),
                (lambda before: '' if not before else 'before:{}'.format(before))(before)
            ),
            'tbm': 'nws',
            'start': 0,
            'hl': 'ru',
            'gl': 'ru'
        }
        self.headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
                          'Chrome/70.0.3538.77 Safari/537.36'
            # 'Cookie': 'CGIC=IgMqLyo; '
            #           '1P_JAR=2020-06-06-20; '
            #           'NID=204=phrZMV6C1pk1e34P2JlDhe_'
            #           '4jxUPa5N0YfZHoCMGWf7IkRelYkBkN6PPV4eqS27lBktHz'
            #           'SWTC6xnqUJEVQQ0qC0dDanrpe-2fpRcV9luZfZ8_VdOFLv9'
            #           'OBp5ixmPpNKOUez3-cMyXD3jAg1uchenXt4wM_uHmTRA5p6YQKIlDl8'
        }
        if not self._check_search_string():
            raise ValueError('Wrong search string')

    def dump(self):
        with Session() as s:
            data = ''
            flag = True
            while flag:
                req = s.get(self.url, params=self.params, headers=self.headers)
                if req.status_code == '429':
                    raise ValueError('Too many requests')
                for url in self._get_data(req.text):
                    if not url:
                        flag = False
                        break
                    data += '{}\n'.format(url)
                self.params['start'] += 10
                sleep(2)
            return BytesIO(data.encode())


def check_date(date):
    try:
        strptime(date, '%Y-%m-%d')
        return True
    except ValueError:
        return False
