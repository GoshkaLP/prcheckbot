from flask import Flask, make_response, request
from config import Config
from flask_sqlalchemy import SQLAlchemy
import telebot
from extensions import GoogleNewsURLDumper, check_date
from os import getenv

token = '1121674909:AAETzxZPRT-rGziD-AWbfC7EpFTTEf3NY4E'
app = Flask(__name__)
app.config.from_object(Config)
bot = telebot.TeleBot(token)
bot.remove_webhook()
secret = 'prcheckbot'
db = SQLAlchemy(app)


class Users(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(255))
    mes_status = db.Column(db.Integer)
    search_string = db.Column(db.String(255))
    after_date = db.Column(db.String(255))
    before_date = db.Column(db.String(255))


@app.route('/ping', methods=['GET', 'HEAD'])
def ping_handler():
    return 'ok', 200


@app.route('/{}'.format(secret), methods=['POST'])
def handler():
    bot.process_new_updates([telebot.types.Update.de_json(request.get_data().decode('utf-8'))])
    return make_response('ok', 200)


@bot.message_handler(commands=['start'])
def start_handler(message):
    bot.send_message(message.chat.id, text='Давайте начнем!\n'
                                           'Для того, чтобы посмотреть список доступных команд, нажмите /help')


@bot.message_handler(commands=['help'])
def help_handler(message):
    mes = '*Доступные команды:*\n' \
          '`/find` - выгрузка ссылок по поисковому запросу,\n\n' \
          '*На данный момент бот работает со следующими поисковиками:*\n' \
          '`Google News`\n\n' \
          '*Версия бота:*\n' \
          '`1.0`'
    bot.send_message(message.chat.id, text=mes, parse_mode='Markdown')


@bot.message_handler(commands=['find'])
def find_handler(message):
    user_id = str(message.from_user.id)
    chat_id = message.chat.id
    user_obj = Users.query.filter_by(user_id=user_id).first()

    if not user_obj:
        db.session.add(Users(user_id=user_id, mes_status=0))
        db.session.commit()

    Users.query.filter_by(user_id=user_id).update({'mes_status': 0})

    bot.send_message(chat_id, text='Отправьте поисковый запрос следующим сообщением')


def start_dumping(chat_id, user_id):
    user_obj = Users.query.filter_by(user_id=user_id).first()
    dump_data = GoogleNewsURLDumper(user_obj.search_string, user_obj.after_date, user_obj.before_date).dump()
    caption = 'По вашему поисковому запросу новостные ссылки были успешно сохранены в файл'
    bot.send_document(chat_id, data=('file.txt', dump_data), caption=caption)


@bot.message_handler(content_types=['text'])
def text_handler(message):
    user_id = str(message.from_user.id)
    chat_id = message.chat.id
    user_obj = Users.query.filter_by(user_id=user_id).first()

    if not user_obj:
        bot.send_message(chat_id, text='Неверная команда! Введите `/help` для просмотра справки',
                         parse_mode='Markdown')

    user_upd_obj = Users.query.filter_by(user_id=user_id)
    if user_obj.mes_status == 0:
        search_string = message.text
        try:
            GoogleNewsURLDumper(search_string)
            user_upd_obj.update({'search_string': search_string, 'mes_status': 1})
            db.session.commit()
            bot.send_message(chat_id, text='Отправьте дату, *с момента которой хотите получить ссылки*\n'
                                           'Или отправьте *Нет*, если не хотите указывать данный параметр\n'
                                           'Формат ввода даты: `YYYY-MM-DD`',
                             parse_mode='Markdown')
        except ValueError as e:
            print(e)
            if str(e) == 'Wrong search string':
                bot.send_message(chat_id, text='*По данному запросу не было найдено ссылок!*',
                                 parse_mode='Markdown')
            elif str(e) == 'Too many requests':
                bot.send_message(chat_id, text='*Превышено количество запросов в Google!\nПодождите немного!*',
                                 parse_mode='Markdown')

    elif user_obj.mes_status == 1:
        after_date = message.text

        if after_date.lower() == 'нет':
            user_upd_obj.update({'mes_status': 2})
            db.session.commit()
            bot.send_message(chat_id, text='Отправьте дату, *по момент которой хотите получить ссылки*\n'
                                           'Или отправьте *Нет*, если не хотите указывать данный параметр\n'
                                           'Формат ввода даты: `YYYY-MM-DD`',
                             parse_mode='Markdown')
        elif check_date(after_date):
            user_upd_obj.update({'mes_status': 2, 'after_date': after_date})
            db.session.commit()
            bot.send_message(chat_id, text='Отправьте дату, *по момент которой хотите получить ссылки*\n'
                                           'Или отправьте *Нет*, если не хотите указывать данный параметр\n'
                                           'Формат ввода даты: `YYYY-MM-DD`',
                             parse_mode='Markdown')
        else:
            bot.send_message(chat_id, text='Вы ввели *неправильный* формат даты или не ответили *Нет*\n'
                                           'Попробуйте еще раз',
                             parse_mode='Markdown')

    elif user_obj.mes_status == 2:
        before_date = message.text

        if before_date.lower() == 'нет':
            user_upd_obj.update({'mes_status': 3})
            db.session.commit()
            bot.send_message(chat_id, text='Начат процесс выгрузки ссылок...\n'
                                           'Между переключениями страниц стоит задержка 2с, чтобы'
                                           ' `Google` не банил за спам',
                             parse_mode='Markdown')
            try:
                start_dumping(chat_id, user_id)
            except ValueError as e:
                if str(e) == 'Too many requests':
                    bot.send_message(chat_id, text='*Произошла ошибка!*\n'
                                                   'Превышено количество запросов в Google!\nПодождите немного!',
                                     parse_mode='Markdown')
                elif str(e) == 'Empty file':
                    bot.send_message(chat_id, text='*Произошла ошибка!*\n'
                                                   'Не удалось выгрузить ссылки с поисковика.\n'
                                                   'Такое бывает, когда Google обрывает запрос.\n'
                                                   'Попробуйте еще раз')

        elif check_date(before_date):
            user_upd_obj.update({'mes_status': 3, 'before_date': before_date})
            db.session.commit()
            bot.send_message(chat_id, text='Начат процесс выгрузки ссылок...\n'
                                           'Между переключениями страниц стоит задержка 2с, чтобы'
                                           ' `Google` не банил за спам',
                             parse_mode='Markdown')
            try:
                start_dumping(chat_id, user_id)
            except ValueError as e:
                if str(e) == 'Too many requests':
                    bot.send_message(chat_id, text='*Произошла ошибка!*\n'
                                                   '*Превышено количество запросов в Google!\nПодождите немного!*',
                                     parse_mode='Markdown')
                elif str(e) == 'Empty file':
                    bot.send_message(chat_id, text='*Произошла ошибка!*\n'
                                                   'Не удалось выгрузить ссылки с поисковика.\n'
                                                   'Такое бывает, когда Google обрывает запрос.\n'
                                                   'Попробуйте еще раз')
        else:
            bot.send_message(chat_id, text='Вы ввели *неправильный* формат даты или не ответили *Нет*\n'
                                           'Попробуйте еще раз',
                             parse_mode='Markdown')

    elif user_obj.mes_status == 3:
        bot.send_message(chat_id, text='Неверная команда!\nНапишите `/help` для получения справки.',
                         parse_mode='Markdown')


# bot.set_webhook('https://3f4af1be1a35.ngrok.io/{}'.format(secret))
# app.run(host='0.0.0.0', port=80)
bot.set_webhook('https://prcheckbot.herokuapp.com/{}'.format(secret))
app.run(host='0.0.0.0', port=getenv('PORT'))

