from flask import Blueprint, request
from .bot import bot, secret
import telebot

node = Blueprint('node', __name__)


@node.route('/{}'.format(secret), methods=['POST'])
def handler():
    bot.process_new_updates([telebot.types.Update.de_json(request.get_data().decode('utf-8'))])
    return 'ok', 200
