import requests
from requests import Session
from bs4 import BeautifulSoup
from time import sleep, strptime
from io import BytesIO


# class ProxyWrapper:
#     def __init__(self, db_table, db_obj):
#         self.db_table = db_table
#         self.db_obj = db_obj
#         self.headers = {
#             'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
#                           'Chrome/70.0.3538.77 Safari/537.36'
#         }
#
#     def _check_proxy(self, proxy_url):
#         url = 'https://google.ru/search'
#         proxy = {'https': proxy_url}
#
#         params = {
#             'q': 'google',
#             'tbm': 'nws',
#             'hl': 'ru',
#             'gl': 'ru'
#         }
#         try:
#             req = requests.get(url, headers=self.headers, params=params, proxies=proxy)
#             soup = BeautifulSoup(req.text, 'lxml')
#             if soup.find('div', class_='g-recaptcha'):
#                 print('recaptcha error')
#                 return False
#             return True
#         except:
#             print('connection error')
#             return False
#
#     def add_proxy(self):
#         url = 'https://www.socks-proxy.net/'
#         req = requests.get(url, headers=self.headers)
#         soup = BeautifulSoup(req.text, 'lxml')
#         data = soup.find('tbody').find_all('tr')
#         print('STARTED')
#         for row in data:
#             td_tags = row.find_all('td')
#             if td_tags[6].text.lower() == 'yes':
#                 protocol = td_tags[4].text.lower()
#                 ip = td_tags[0].text
#                 port = td_tags[1].text
#                 proxy_url = '{}://{}:{}'.format(protocol, ip, port)
#                 if self._check_proxy(proxy_url):
#                     print(proxy_url)
#                     self.db_obj.session.add(self.db_table(proxy_url=proxy_url))
#                     self.db_obj.session.commit()
#
#     def get_proxy(self):
#         proxy_url = self.db_table.query.order_by(func.random()).first()
#         if not proxy_url:
#             self.add_proxy()
#             self.get_proxy()
#         if not self._check_proxy(proxy_url.proxy_url):
#             self.db_obj.session.delete(proxy_url)
#             self.db_obj.session.commit()
#             self.get_proxy()
#         return proxy_url.proxy_url


class GoogleNewsURLDumper:
    def _get_data(self, request_text):
        print(request_text)
        soup = BeautifulSoup(request_text, 'lxml')
        if soup.find('div', class_='g-recaptcha'):
            raise ValueError('Too many requests')
        data = soup.find_all('div', class_='ts')
        if not data:
            data = soup.find_all('g-card')
            if not data:
                yield None
        for elem in data:
            url = elem.find('a', href=True)['href']
            yield url

    def _check_search_string(self):
        req = requests.get(self.url, params=self.params, headers=self.headers, proxies=self.proxy)
        for x in self._get_data(req.text):
            if not x:
                return False
            else:
                break
        return True

    def __init__(self, search_string, proxy, after=None, before=None):
        self.url = 'https://www.google.ru/search'
        self.proxy = {'http': proxy}
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
        }
        if not self._check_search_string():
            raise ValueError('Wrong search string')

    def dump(self):
        data = ''
        flag = True
        print('HERE', self.proxy)
        with Session() as s:
            while flag:
                req = s.get(self.url, params=self.params, headers=self.headers, proxies=self.proxy)
                for url in self._get_data(req.text):
                    if not url:
                        flag = False
                        break
                    data += '{}\n'.format(url)
                self.params['start'] += 10
                sleep(2)
            if not data:
                raise ValueError('Empty file')
            return BytesIO(data.encode())


def check_date(date):
    try:
        strptime(date, '%Y-%m-%d')
        return True
    except ValueError:
        return False
