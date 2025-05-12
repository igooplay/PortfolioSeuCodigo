import os
import pymysql

# Configure PyMySQL to be used by SQLAlchemy with MySQL
pymysql.install_as_MySQLdb()

# MySQL connection settings
MYSQL_USER = os.environ.get('MYSQL_USER', 'admin@seucodigo.shop')
MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', 'admin123')
MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
MYSQL_PORT = os.environ.get('MYSQL_PORT', '3306')
MYSQL_DATABASE = os.environ.get('MYSQL_DATABASE', 'seucodigo')

# MySQL connection string for SQLAlchemy
MYSQL_CONNECTION_STRING = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"

# MySQL charset and collation settings
MYSQL_CHARSET = 'utf8mb4'
MYSQL_COLLATION = 'utf8mb4_unicode_ci'