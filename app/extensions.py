import requests
from requests import Session
import psycopg2
from time import strptime, sleep
from datetime import datetime
from bs4 import BeautifulSoup
from io import BytesIO


class Psql:
    def __init__(self, database, username, password, host, port):
        self.database = database
        self.usernmame = username
        self.password = password
        self.host = host
        self.port = port

    def _conn(self):
        return psycopg2.connect(
            database=self.database,
            user=self.usernmame,
            password=self.password,
            host=self.host,
            port=self.port
        )

    def exec(self, query):
        db_conn = self._conn()
        cursor = db_conn.cursor()
        cursor.execute(query)
        if ('INSERT' in query) or ('UPDATE' in query) or ('DELETE' in query):
            db_conn.commit()
        elif 'SELECT' in query:
            data = (row for row in cursor)
            return data
        db_conn.close()


db = Psql('prcheckbot', 'pradmin', 'a8D2I5iob9oO', '23.111.204.159', '5430')


def check_user_db(user_id):
    flag = next(db.exec("SELECT EXISTS(SELECT user_id FROM Users WHERE user_id='{}')".format(user_id)))[0]
    if not flag:
        db.exec("INSERT INTO Users(user_id) VALUES('{}')".format(user_id))


def number_of_users():
    result = next(db.exec("SELECT count(*) FROM Users"))[0]
    return result


class ProxyWrapper:
    def __init__(self):
        self.headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
                          'Chrome/70.0.3538.77 Safari/537.36'
        }

    def _check_proxy(self, proxy_url):
        url = 'https://google.ru/search'
        proxy = {'https': proxy_url}

        params = {
            'q': 'google',
            'tbm': 'nws',
            'hl': 'ru',
            'gl': 'ru'
        }

        try:
            req = requests.get(url, headers=self.headers, params=params, proxies=proxy)
            soup = BeautifulSoup(req.text, 'lxml')
            if soup.find('div', class_='g-recaptcha'):
                print('recaptcha error')
                return False
            return True
        except:
            print('connection error')
            return False

    def add_proxy(self):
        db.exec('DELETE FROM Proxy')
        token = '738fe198fb-6c257969da-c933262191'
        url = 'https://proxy6.net/api/{}/getproxy'.format(token)
        req = requests.get(url)
        data = req.json()['list']
        for key in data.keys():
            pr = data[key]
            if pr['active'] == '1':
                proxy_url = 'https://{}:{}@{}:{}'.format(pr['user'], pr['pass'], pr['host'], pr['port'])
                if self._check_proxy(proxy_url):
                    db.exec("INSERT INTO Proxy (proxy_url) VALUES ('{}')".format(proxy_url))

    def get_proxy(self):
        n = next(db.exec('SELECT COUNT(*) FROM Proxy'))[0]
        if n == 0:
            self.add_proxy()
            self.get_proxy()
        proxy_url = next(db.exec('SELECT proxy_url FROM Proxy OFFSET floor(random()*{}) LIMIT 1'.format(n)))[0]
        if not self._check_proxy(proxy_url):
            db.exec("DELETE FROM Proxy WHERE proxy_url = '{}'".format(proxy_url))
            self.get_proxy()
        return proxy_url


class GoogleNewsURLDumper:
    def _get_data(self, request_text):
        # with open('test.html', 'w') as file:
        #     file.write(request_text)
        # print(request_text)
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

    def __init__(self, search_string, proxy_obj, after=None, before=None, language='ru', country='ru'):
        self.url = 'https://www.google.ru/search'
        self.proxy = {'https': proxy_obj.get_proxy()}
        self.params = {
            'q': '{} {} {}'.format(
                search_string,
                (lambda after: '' if not after else 'after:{}'.format(after))(after),
                (lambda before: '' if not before else 'before:{}'.format(before))(before)
            ),
            'tbm': 'nws',
            'start': 0,
            'hl': language,
            'gl': country
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
    except ValueError:
        raise ValueError('Wrong date')


def get_current_date():
    return datetime.today().strftime('%Y-%m-%d')


def get_countries():
    data = db.exec('SELECT country FROM Countries')
    return data


def get_country_code(country):
    code = next(db.exec("SELECT country_code FROM Countries WHERE country='{}'".format(country)))[0]
    if not code:
        raise ValueError('Wrong country')
    return code


def get_languages():
    data = db.exec('SELECT language FROM Languages')
    return data


def get_language_code(country):
    code = next(db.exec("SELECT language_code FROM Languages WHERE language='{}'".format(country)))[0]
    if not code:
        raise ValueError('Wrong language')
    return code


class Users:
    def __init__(self, user_id):
        self.user_id = user_id

    def set_param(self, param_key, param):
        db.exec("UPDATE Users SET {}='{}' WHERE user_id='{}'".format(param_key, param, self.user_id))

    def get_params(self):
        data = next(db.exec("SELECT search_string, after_date, before_date, country, language FROM Users "
                            "WHERE user_id='{}'".format(self.user_id)))
        return data

    def remove_dates(self):
        db.exec("UPDATE Users SET after_date=NULL, before_date=NULL WHERE user_id='{}'".format(self.user_id))
