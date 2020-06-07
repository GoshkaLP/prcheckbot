from flask import Blueprint, request
from .bot import bot, secret
import telebot
from .extensions import ProxyWrapper

node = Blueprint('node', __name__)


@node.route('/{}'.format(secret), methods=['POST'])
def handler():
    bot.process_new_updates([telebot.types.Update.de_json(request.get_data().decode('utf-8'))])
    return 'ok', 200


@node.route('/{}/check_proxy'.format(secret), methods=['GET'])
def check_proxy_handler():
    ProxyWrapper().add_proxy()
    return 'Done!', 200
