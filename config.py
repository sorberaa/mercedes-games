import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# Путь к файлу базы данных SQLite
DB_PATH = BASE_DIR / "amg_game.db"

# Игровые константы
START_COINS = 1000
MAX_FUEL = 100
FUEL_REGEN_INTERVAL_SEC = 180  # +5 топлива каждые 3 минуты
FUEL_REGEN_AMOUNT = 5
RACE_FUEL_COST = 10
BOSS_ATTACK_FUEL_COST = 15
NITRO_ATTACK_FUEL_COST = 25

# ID администраторов (строго только указанные лица)
ADMIN_IDS_RAW = os.getenv("ADMIN_IDS", "7834400921,8936384717")
ADMIN_IDS = [int(x.strip()) for x in ADMIN_IDS_RAW.split(",") if x.strip().isdigit()]
if not ADMIN_IDS:
    ADMIN_IDS = [7834400921, 8936384717]

# Гифки с дикобразами
PORCUPINE_GIFS = [
    "https://media.giphy.com/media/l41JRsph73VokN6ik/giphy.gif",
    "https://media.giphy.com/media/3o7TKMt1VVNkHV2PaE/giphy.gif",
    "https://media.giphy.com/media/26AHONQ79FdWZhAI0/giphy.gif"
]

