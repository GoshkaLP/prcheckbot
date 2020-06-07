import telebot
from .extensions import GoogleNewsURLDumper, FindMessageParse, ProxyWrapper, Logs, AddMessageParse

token = '1121674909:AAETzxZPRT-rGziD-AWbfC7EpFTTEf3NY4E'
webhook_url = 'https://prcheckbot.herokuapp.com'
bot = telebot.TeleBot(token)
bot.remove_webhook()
secret = 'prcheckbot'
proxy_obj = ProxyWrapper()


@bot.message_handler(commands=['start'])
def start_handler(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, text='Давайте начнем!\n'
                                   'Для того, чтобы посмотреть список доступных команд, нажмите /help')


@bot.message_handler(commands=['help'])
def help_handler(message):
    chat_id = message.chat.id
    mes = '*Доступные команды:*\n' \
          '`/find поисковый_запрос from[YYYY-MM-DD] to[YYYY-MM-DD]` - выгрузка ссылок по поисковому запросу,\n' \
          'где `from[YYYY-MM-DD]` и `to[YYYY-MM-DD]` - опциональные параметры\n' \
          '`/add token` - привязать свой токен\n' \
          '`/logs` - выгрузить логи поисковых запросов пользователей\n\n' \
          '*Примеры использования:*\n' \
          '`/find Коронавирус Россия from[2020-05-20] to[2020-06-06]`\n' \
          '`/add Ujh32ls123df`\n\n' \
          '*На данный момент бот работает со следующими поисковиками:*\n' \
          '`Google News`\n\n' \
          '*Версия бота:*\n' \
          '`1.0`'
    bot.send_message(chat_id, text=mes, parse_mode='Markdown')


@bot.message_handler(commands=['find'])
def find_handler(message):
    chat_id = message.chat.id
    try:
        data = FindMessageParse(message.text).result()
        search_string = data['search_string']
        before_date = data['before_date']
        after_date = data['after_date']
        try:
            bot.send_message(chat_id, text='Пытаемся выгрузить ссылки...')
            dump_data = GoogleNewsURLDumper(search_string, proxy_obj, after_date, before_date).dump()
            caption = 'По вашему поисковому запросу новостные ссылки были успешно сохранены в файл'
            bot.send_document(chat_id, data=('file.txt', dump_data), caption=caption)
            Logs(message.from_user, search_string, after_date, before_date).add()
        except ValueError as er:
            if str(er) == 'Wrong search string':
                bot.send_message(chat_id, text='*Ошибка!\n'
                                               'По вашему поисковому запросу не было найдено результатов!*',
                                 parse_mode='Markdown')
            elif str(er) == 'Too many requests':
                bot.send_message(chat_id, text='*Ошибка!\n'
                                               'Вы превысили количество запросов в Google,'
                                               'подождите немного!*', parse_mode='Markdown')
            elif str(er) == 'Empty file':
                bot.send_message(chat_id, text='*Ошибка!\nНе удалось выгрузить ссылки!*', parse_mode='Markdown')
    except ValueError as e:
        if str(e) == 'Wrong date':
            bot.send_message(chat_id, text='*Ошибка!\nНеверный формат даты!*', parse_mode='Markdown')
        elif str(e) == 'No search string':
            bot.send_message(chat_id, text='*Ошибка!\nВы не указали поисковый запрос!*', parse_mode='Markdown')


@bot.message_handler(commands=['add'])
def add_handler(message):
    chat_id = message.chat.id
    try:
        add_obj = AddMessageParse(message.text, message.from_user.id)
        if add_obj.check():
            bot.send_message(chat_id, text='*Вы успешно привязали свой токен!*', parse_mode='Markdown')
        else:
            bot.send_message(chat_id, text='*Ошибка!\nНеверный токен!*', parse_mode='Markdown')
    except ValueError as e:
        if str(e) == 'No token':
            bot.send_message(chat_id, text='*Ошибка!\nВы не указали свой токен!*', parse_mode='Markdown')


@bot.message_handler(commands=['logs'])
def log_handler(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, text='Пытаемся выгрузить логи...')
    try:
        logs = Logs(message.from_user).get()
        caption = 'Логи были успешно выгружены в файл'
        bot.send_document(chat_id, data=('logs.txt', logs), caption=caption)
    except ValueError as e:
        if str(e) == 'Not allowed':
            bot.send_message(chat_id, text='*Ошибка!\nВы не указали свой токен!*', parse_mode='Markdown')
        elif str(e) == 'Empty file':
            bot.send_message(chat_id, text='*Ошибка!\nНе удалось выгрузить логи!*', parse_mode='Markdown')


bot.set_webhook('{}/{}'.format(webhook_url, secret))
