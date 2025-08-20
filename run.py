import os
from app import create_app
from app.config import config

# 根據環境變數決定配置
config_name = os.environ.get('FLASK_ENV', 'development')
app = create_app(config.get(config_name, config['default']))

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000, debug=app.config['DEBUG'])