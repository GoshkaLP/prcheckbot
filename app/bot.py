import telebot
from telebot import types

from .extensions import GoogleNewsURLDumper, ProxyWrapper, Users, check_user_db, check_date, number_of_users, \
    get_countries, get_country_code, get_languages, get_language_code, get_current_date

token = '1039465196:AAFZRdxJxTsxKZIM5Lgb0f_pf-psD7ssfQY'
# webhook_url = 'https://hrspot.me:1234'
webhook_url = 'https://994f1b49f77f.ngrok.io'
bot = telebot.TeleBot(token)
bot.remove_webhook()
secret = 'prcheckbot'
proxy_obj = ProxyWrapper()


@bot.message_handler(commands=['start'])
def start_handler(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    check_user_db(user_id)
    bot.send_message(chat_id, text='Давайте начнем!\n'
                                   'Для того, чтобы посмотреть список доступных команд, нажмите /help')


@bot.message_handler(commands=['help'])
def help_handler(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    check_user_db(user_id)
    mes = '*Доступные команды:*\n' \
          '`/find` - выгрузка ссылок по поисковому запросу,\n' \
          '`/number_users` - узнать количество уникальных пользователей бота\n\n' \
          '*Бот работает со следующими поисковиками:*\n' \
          '`Google News`\n\n' \
          '*Версия бота:*\n' \
          '`1.1`'
    bot.send_message(chat_id, text=mes, parse_mode='Markdown')


@bot.message_handler(commands=['find'])
def find_handler(message):
    user_id = message.from_user.id
    check_user_db(user_id)
    markup = types.ReplyKeyboardRemove()
    msg = bot.reply_to(message, 'Введите поисковый запрос', reply_markup=markup)
    bot.register_next_step_handler(msg, process_search_string_step)


def process_search_string_step(message):
    try:
        user_id = message.from_user.id
        try:
            GoogleNewsURLDumper(message.text, proxy_obj)
            Users(user_id).set_param('search_string', message.text)
            markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
            markup.add('Да')
            markup.add('Нет')
            msg = bot.reply_to(message, 'Хотите ли Вы указать временной промежуток для поискового запроса?',
                               reply_markup=markup)
            bot.register_next_step_handler(msg, process_time_step)
        except ValueError as e:
            if str(e) == 'Wrong search string':
                bot.reply_to(message, text='*Произошла ошибка!\n*'
                                           '*Неверный поисковый запрос!*', parse_mode='Markdown')
    except Exception as er:
        bot.reply_to(message, text='*Произошла ошибка!\n*'
                                   '*Попробуйте еще раз!*', parse_mode='Markdown')


def process_time_step(message):
    try:
        if message.text == 'Нет':
            user_id = message.from_user.id
            Users(user_id).remove_dates()
            markup = types.ReplyKeyboardMarkup(one_time_keyboard=False)
            countries = get_countries()
            for country in countries:
                markup.add(country[0])
            msg = bot.reply_to(message, text='Выберите страну поиска',
                               reply_markup=markup)
            bot.register_next_step_handler(msg, process_region_step)
        elif message.text == 'Да':
            markup = types.ReplyKeyboardRemove()
            mes = 'Отправьте дату, *с момента которой* хотите получить ссылки.\n' \
                  'Формат ввода даты: `YYYY-MM-DD`'
            msg = bot.reply_to(message, mes, parse_mode='Markdown', reply_markup=markup)
            bot.register_next_step_handler(msg, process_after_date_step)
    except Exception as er:
        bot.reply_to(message, text='*Произошла ошибка!\n*'
                                   '*Попробуйте еще раз!*', parse_mode='Markdown')


def process_after_date_step(message):
    try:
        user_id = message.from_user.id
        try:
            check_date(message.text)
            Users(user_id).set_param('after_date', message.text)
            mes = 'Нажмите на кнопку *Текущая дата* или отправьте дату, *по момент которой*,' \
                  'хотите получить ссылки.\n' \
                  'Формат ввода даты: `YYYY-MM-DD`'
            markup = types.ReplyKeyboardMarkup(one_time_keyboard=False)
            markup.add('Текущая дата')
            msg = bot.reply_to(message, mes, parse_mode='Markdown', reply_markup=markup)
            bot.register_next_step_handler(msg, process_before_date_step)
        except ValueError as e:
            if str(e) == 'Wrong date':
                bot.reply_to(message, text='*Произошла ошибка!\n*'
                                           '*Неверный формат даты!*', parse_mode='Markdown')
    except Exception as er:
        print(er)
        bot.reply_to(message, text='*Произошла ошибка!\n*'
                                   '*Попробуйте еще раз!*', parse_mode='Markdown')


def process_before_date_step(message):
    try:
        user_id = message.from_user.id
        try:
            date = message.text
            if message.text == 'Текущая дата':
                date = get_current_date()
            check_date(date)
            Users(user_id).set_param('before_date', date)
            markup = types.ReplyKeyboardMarkup(one_time_keyboard=False)
            countries = get_countries()
            for country in countries:
                markup.add(country[0])
            msg = bot.reply_to(message, text='Выберите страну поиска',
                               reply_markup=markup)
            bot.register_next_step_handler(msg, process_region_step)
        except ValueError as e:
            if str(e) == 'Wrong date':
                bot.reply_to(message, text='*Произошла ошибка!\n*'
                                           '*Неверный формат даты!*', parse_mode='Markdown')
    except Exception as er:
        bot.reply_to(message, text='*Произошла ошибка!\n*'
                                   '*Попробуйте еще раз!*', parse_mode='Markdown')


def process_region_step(message):
    try:
        user_id = message.from_user.id
        try:
            country = get_country_code(message.text)
            Users(user_id).set_param('country', country)
            markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
            languages = get_languages()
            for language in languages:
                markup.add(language[0])
            msg = bot.reply_to(message, text='Выберите язык поиска',
                               reply_markup=markup)
            bot.register_next_step_handler(msg, process_language_and_search_step)
        except ValueError as e:
            if str(e) == 'Wrong country':
                bot.reply_to(message, text='*Произошла ошибка!\n*'
                                           '*Неверный регион!*', parse_mode='Markdown')
    except Exception as er:
        print(er)
        bot.reply_to(message, text='*Произошла ошибка!\n*'
                                   '*Попробуйте еще раз!*', parse_mode='Markdown')


def process_language_and_search_step(message):
    chat_id = message.chat.id
    try:
        user_id = message.from_user.id
        try:
            language = get_language_code(message.text)
            Users(user_id).set_param('language', language)
            user_params = Users(user_id).get_params()
            markup = types.ReplyKeyboardRemove()
            bot.send_message(chat_id, text='Начат процесс выгрузки ссылок...', reply_markup=markup)
            dump_data = GoogleNewsURLDumper(user_params[0], proxy_obj, user_params[1], user_params[2],
                                            user_params[3], user_params[4]).dump()
            caption = 'По вашему поисковому запросу новостные ссылки были успешно сохранены в файл'
            bot.send_document(chat_id, data=('file.txt', dump_data), caption=caption)
        except ValueError as e:
            if str(e) == 'Wrong language':
                bot.reply_to(message, text='*Произошла ошибка!\n*'
                                           '*Неверный язык!*', parse_mode='Markdown')
            elif str(e) == 'Wrong search string':
                bot.reply_to(message, text='*Произошла ошибка!\n*'
                                           '*Неверный поисковый запрос!*', parse_mode='Markdown')
            elif str(e) == 'Empty file':
                bot.reply_to(message, text='*Произошла ошибка!\n*'
                                           '*Не удалось выгрузить ссылки!*', parse_mode='Markdown')
            elif str(e) == 'Too many requests':
                bot.reply_to(message, text='*Произошла ошибка!\n*'
                                           '*Слишком много запросов в поисковик!*\n'
                                           '*Подождите немного!*', parse_mode='Markdown')
    except Exception as er:
        print(er)
        bot.reply_to(message, text='*Произошла ошибка!\n*'
                                   '*Попробуйте еще раз!*', parse_mode='Markdown')


@bot.message_handler(commands=['number_users'])
def number_users_handler(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    check_user_db(user_id)
    amount = number_of_users()
    mes = 'Количество пользователей бота: {}'.format(amount)
    bot.send_message(chat_id, text=mes, parse_mode='Markdown')


bot.set_webhook('{}/{}'.format(webhook_url, secret))
