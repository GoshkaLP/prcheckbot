import requests
from requests import Session
import psycopg2
import re
from time import strptime
from bs4 import BeautifulSoup
from time import sleep
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


class Logs:
    def __init__(self, user_obj, search_string=None, after_date=None, before_date=None):
        self.user_obj = user_obj
        self.search_string = search_string
        self.after_date = after_date
        self.before_date = before_date

    def _get_username(self):
        username = self.user_obj.username
        if not self.user_obj.username:
            username = '{} {}'.format(self.user_obj.first_name, self.user_obj.last_name)
        return username

    def add(self):
        username = self._get_username()
        user_id = str(self.user_obj.id)
        sql_query = "INSERT INTO Logs (user_id, username, search_string, after_date, before_date) VALUES ('{}', '{}', '{}', '{}', '{}')".\
            format(user_id, username, self.search_string, self.after_date, self.before_date)
        db.exec(sql_query)

    def get(self):
        user_id = str(self.user_obj.id)
        flag = next(db.exec("SELECT allow FROM Users WHERE user_id = '{}'".format(user_id)))[0]
        if flag:
            data = db.exec('SELECT username, search_string, after_date, before_date FROM Logs')
            res = ''
            for row in data:
                username = row[0]
                search_string = row[1]
                after_date = row[2]
                before_date = row[3]
                res += '{} searched: {} {} {}\n'.format(username, search_string, after_date, before_date)
            if not res:
                raise ValueError('Empty file')
            return BytesIO(res.encode())
        else:
            raise ValueError('Not allowed')


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
        proxy_url = next(db.exec('SELECT proxy_url FROM Proxy OFFSET floor(random()*{}) LIMIT 1'.format(n)))[0]
        if not proxy_url:
            self.add_proxy()
            self.get_proxy()
        if not self._check_proxy(proxy_url):
            db.exec("DELETE FROM Proxy WHERE proxy_url = '{}'".format(proxy_url))
            self.get_proxy()
        return proxy_url


class GoogleNewsURLDumper:
    def _get_data(self, request_text):
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

    def __init__(self, search_string, proxy_obj, after=None, before=None):
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


class FindMessageParse:
    def __init__(self, mes):
        self.mes = mes

    def _check_date(self, date):
        try:
            strptime(date, '%Y-%m-%d')
            return True
        except ValueError:
            return False

    def _find_params(self, mes):
        new_mes = mes
        after_pattern = re.compile('from\[.{0,10}\]')
        before_pattern = re.compile('to\[.{0,10}\]')
        date_pattern = re.compile('\d{4}-\d{2}-\d{2}')
        after_date = None
        before_date = None
        tmp_after = after_pattern.search(new_mes)
        if tmp_after:
            date = date_pattern.search(tmp_after.group())
            if not date:
                raise ValueError('Wrong date')
            if self._check_date(date.group()):
                after_date = date.group()
                new_mes = re.sub(after_pattern, '', new_mes)
            else:
                raise ValueError('Wrong date')
        tmp_before = before_pattern.search(new_mes)
        if tmp_before:
            date = date_pattern.search(tmp_before.group())
            if not date:
                raise ValueError('Wrong date')
            if self._check_date(date.group()):
                before_date = date.group()
                new_mes = re.sub(before_pattern, '', new_mes)
            else:
                raise ValueError("Wrong date")
        new_mes = new_mes.strip()
        if not new_mes:
            raise ValueError('No search string')
        return {
            'search_string': new_mes,
            'before_date': before_date,
            'after_date': after_date,
        }

    def result(self):
        if self.mes == '/find':
            raise ValueError('No search string')
        else:
            data = self._find_params(self.mes[6:])
            return data


class AddMessageParse:
    def __init__(self, mes, user_id):
        self.mes = mes
        self.user_id = user_id

    def _get_token(self):
        if self.mes == '/add':
            raise ValueError('No token')
        else:
            token = self.mes.split()[1]
            return token

    def check(self):
        flag1 = next(db.exec("SELECT EXISTS(SELECT token FROM Users WHERE user_id='{}')".format(self.user_id)))[0]
        if not flag1:
            raise ValueError('Lack of token')
        flag2 = next(db.exec("SELECT allow FROM Users WHERE user_id='{}'".format(self.user_id)))[0]
        if flag2:
            raise ValueError('Already allowed')
        true_token = next(db.exec("SELECT token FROM Users WHERE user_id = '{}'".format(self.user_id)))[0]
        if true_token == self._get_token():
            db.exec("UPDATE Users SET allow = True WHERE user_id = '{}'".format(self.user_id))
            return True
        return False
