import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(__file__)
KV_DIR = os.path.join(BASE_DIR, 'view', 'kv')
VIEW_DIR = os.path.join(BASE_DIR, 'view', 'screens')
CONTROLLER_DIR = os.path.join(BASE_DIR, 'controller')

DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")