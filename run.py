from app import create_app
from config import Config
from os import getenv

app = create_app(Config)

if __name__ == '__main__':
    # app.run(host='0.0.0.0', port=80)
    app.run(host='0.0.0.0', port=getenv('PORT'))
