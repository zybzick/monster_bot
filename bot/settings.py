import os
from dotenv import load_dotenv


DEFAULT_PREFIX = 'L'

SETTINGS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SETTINGS_DIR)
DATA_DIR = os.path.join(ROOT_DIR, 'data')

# Dotenv Conf
dotenv_path = os.path.join(SETTINGS_DIR, '../.env')

if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

# Discord Conf
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", False)

# PostgreSQL conf
POSTGRES_PASS = os.getenv("POSTGRES_PASS", False)
POSTGRES_USER = os.getenv("POSTGRES_USER", False)
POSTGRES_DB = os.getenv("POSTGRES_DB", False)
POSTGRES_HOST = os.getenv("POSTGRES_HOST", False)
