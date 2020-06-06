from requests import Session
import requests
from bs4 import BeautifulSoup
from time import sleep, strptime
from io import BytesIO


def paste_config(option, text=None, code=None):
    api_dev_key = '137511a516aab817743d7c0e0a4de528'
    api_user_key = 'd99e1aa5ee7fba779e5d4286086de3a8'
    url = 'https://pastebin.com/api/api_post.php'
    data = {
        'api_dev_key': api_dev_key,
        'api_option': option,
        'api_user_key': api_user_key
    }
    if option == 'paste':
        data['api_paste_expire_date'] = '2W'
        data['api_paste_private'] = '1'
        data['api_paste_code'] = text
        req = requests.post(url, data=data)
        code = req.text[-req.text[::-1].index('/'):]
        return code
    elif option == 'delete':
        data['api_paste_key'] = code
        requests.post(url, data=data)


def get_paste(code):
    url = 'https://pastebin.com/raw/'+code
    req = requests.get(url)
    return req.text


class GoogleNewsURLDumper:
    def _get_data(self, request_text):
        #
        print(paste_config('paste', request_text))
        #
        soup = BeautifulSoup(request_text, 'lxml')
        data = soup.find_all('div', class_='ts')
        if not data:
            yield None
        for ts in data:
            url = ts.find('a')['href']
            yield url

    def _check_search_string(self):
        req = requests.get(self.url, params=self.params, headers=self.headers)
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
