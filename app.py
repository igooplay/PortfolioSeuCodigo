import os
import logging

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_login import LoginManager
from flask_cors import CORS
from flask_socketio import SocketIO

# Importe a configuração MySQL
import mysql_config

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create SQLAlchemy base class
class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy with the Base class
db = SQLAlchemy(model_class=Base)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or os.urandom(24)
app.config['WTF_CSRF_SECRET_KEY'] = os.environ.get("CSRF_SECRET_KEY") or os.urandom(24)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  # needed for url_for to generate with https

# Enable CORS
CORS(app)

# Initialize Socket.IO com modo assíncrono eventlet e configurações otimizadas
socketio = SocketIO(
    app, 
    cors_allowed_origins="*", 
    async_mode='eventlet',
    ping_timeout=60,
    ping_interval=25,
    engineio_logger=True,
    ssl_context='adhoc'
)

# Configure database connection
# Verifica se estamos usando PostgreSQL (variável de ambiente DATABASE_URL) ou MySQL
db_url = os.environ.get("DATABASE_URL")
using_postgres = db_url is not None and db_url.startswith('postgres')

if using_postgres:
    # Configuração para PostgreSQL
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True
    }
else:
    # Configuração para MySQL
    app.config["SQLALCHEMY_DATABASE_URI"] = mysql_config.MYSQL_CONNECTION_STRING
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
        "connect_args": {
            "charset": mysql_config.MYSQL_CHARSET
        }
    }
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize the database with the app
db.init_app(app)

# Configure context processor para disponibilizar as configurações
@app.context_processor
def inject_site_config():
    from models import SiteConfig
    return {'site_config': SiteConfig.get_settings()}

# Configure login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor, faça login para acessar esta página.'
login_manager.login_message_category = 'info'

# Import models and create tables within app context
with app.app_context():
    # Import models here to avoid circular imports
    from models import User, Project, Service, Testimonial, ChatMessage
    
    db.create_all()

# Import routes after models are created
from routes import *

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
