from flask import Flask
from .node import node


def create_app(config):
    app = Flask(__name__, instance_relative_config=False)

    app.config.from_object(config)

    app.register_blueprint(node)

    return app
