import logging
from datetime import datetime, timedelta
from typing import Optional, List
import sqlite3
import os
import ast
import time
from pathlib import Path
import asyncio

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    CallbackContext
)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("taxibot_logs.log", encoding='utf-8'),  # <-- Лог-файл будет тут же, где запускается бот
        logging.StreamHandler()  # чтобы не потерять вывод в консоль
    ]
)

# === ПРОВЕРКА НАЛИЧИЯ В ЧЕРНОМ ЛИСТЕ ===

def get_black_list_check(user_id) -> bool:
    
    try:
        gen_path = Path(__file__).parent
        # print('GEN PATH: ', gen_path)
        black_list_path = gen_path / 'data'
        black_list_path = black_list_path / 'black_list.txt'

        # print('BL PATH: ', black_list_path)
        with open(black_list_path, 'r', encoding='utf-8') as file:
            data = file.read()
            black_list = ast.literal_eval(data)
        # print('BL LIST CONTAIN: ', black_list)
        # print('BL LIST TYPE: ', type(black_list))
        
        if user_id in black_list:
            return True
        else:
            return False
    except:
        return False
    
    
# === КОНСТАНТЫ И НАСТРОЙКИ ===
TG_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# === СТАТУСЫ FSM ===
(
    WAIT_CONTACT_CHOICE, WAIT_PHONE,  # <--- новые состояния
    START,
    ENTER_DATE,
    ENTER_TIME,
    ENTER_PASS_QNT,
    ENTER_DEPARTURE,
    ENTER_DESTINATION,
    ENTER_TIME_WINDOW,
    ENTER_COMMENT,
    CONFIRM_REQUEST,
    DELETE_REQUEST,
    DELETE_REASON,
    ANNOUNCEMENT_START,
    ANNOUNCEMENT_SEND
) = range(15)

# === ТОЧКИ МАРШРУТА (с клавиатурой) ===
VALID_POINTS = {
    'а/п Шереметьево', 'а/п Домодедово', 'а/п Внуково', 'а/п Рощино',
    'ст.м. Домодедовская', 'ст.м. Ховрино',
    'ж/д Павелецкий', 'ж/д Восточный', 'ж/д Три вокзала', 'ж/д Курский', 'ж/д Тюмень',
    'отель "Салют"', 'отель "Уют"', 'отель "Ибис-Домодедово"', 'отель "Виктория" (Тюмень)'
}

# POINTS_KEYBOARD_FROM = [
#     [InlineKeyboardButton("✈️ ИЗ ↗️ а/п Шереметьево", callback_data="point_а/п Шереметьево")],
#     [InlineKeyboardButton("✈️ ИЗ ↗️ а/п Домодедово", callback_data="point_а/п Домодедово")],
#     [InlineKeyboardButton("✈️ ИЗ ↗️ а/п Внуково", callback_data="point_а/п Внуково")],
#     [InlineKeyboardButton("✈️ ИЗ ↗️ а/п Рощино", callback_data="point_а/п Рощино")],
#     [InlineKeyboardButton("🚇 ИЗ ↗️ ст.м. Домодедовская", callback_data="point_ст.м. Домодедовская")],
#     [InlineKeyboardButton("🚇 ИЗ ↗️ ст.м. Ховрино", callback_data="point_ст.м. Ховрино")],
#     [InlineKeyboardButton("🚂 ИЗ ↗️ ж/д Павелецкий", callback_data="point_ж/д Павелецкий")],
#     [InlineKeyboardButton("🚂 ИЗ ↗️ ж/д Восточный", callback_data="point_ж/д Восточный")],
#     [InlineKeyboardButton("🚂 ИЗ ↗️ ж/д Три вокзала", callback_data="point_ж/д Три вокзала")],
#     [InlineKeyboardButton("🚂 ИЗ ↗️ ж/д Курский", callback_data="point_ж/д Курский")],
#     [InlineKeyboardButton("🚂 ИЗ ↗️ ж/д Тюмень", callback_data="point_ж/д Тюмень")],
#     [InlineKeyboardButton("🏨 ИЗ ↗️ отель 'Салют'", callback_data="point_отель \"Салют\"")],
#     [InlineKeyboardButton("🏨 ИЗ ↗️ отель 'Уют'", callback_data="point_отель \"Уют\"")],
#     [InlineKeyboardButton("🏨 ИЗ ↗️ отель 'Ибис-Домодедово'", callback_data="point_отель \"Ибис-Домодедово\"")],
#     [InlineKeyboardButton("🏨 ИЗ ↗️ отель 'Виктория (Тюмень)'", callback_data="point_отель \"Виктория (Тюмень)\"")]
#     ]

# POINTS_KEYBOARD_TO = [
#     [InlineKeyboardButton("✈️ В ↘️ а/п Шереметьево", callback_data="point_а/п Шереметьево")],
#     [InlineKeyboardButton("✈️ В ↘️ а/п Домодедово", callback_data="point_а/п Домодедово")],
#     [InlineKeyboardButton("✈️ В ↘️ а/п Внуково", callback_data="point_а/п Внуково")],
#     [InlineKeyboardButton("✈️ В ↘️ а/п Рощино", callback_data="point_а/п Рощино")],
#     [InlineKeyboardButton("🚇 В ↘️ ст.м. Домодедовская", callback_data="point_ст.м. Домодедовская")],
#     [InlineKeyboardButton("🚇 В ↘️ ст.м. Ховрино", callback_data="point_ст.м. Ховрино")],
#     [InlineKeyboardButton("🚂 В ↘️ ж/д Павелецкий", callback_data="point_ж/д Павелецкий")],
#     [InlineKeyboardButton("🚂 В ↘️ ж/д Восточный", callback_data="point_ж/д Восточный")],
#     [InlineKeyboardButton("🚂 В ↘️ ж/д Три вокзала", callback_data="point_ж/д Три вокзала")],
#     [InlineKeyboardButton("🚂 В ↘️ ж/д Курский", callback_data="point_ж/д Курский")],
#     [InlineKeyboardButton("🚂 В ↘️ ж/д Тюмень", callback_data="point_ж/д Тюмень")],
#     [InlineKeyboardButton("🏨 В ↘️ отель 'Салют'", callback_data="point_отель \"Салют\"")],
#     [InlineKeyboardButton("🏨 В ↘️ отель 'Уют'", callback_data="point_отель \"Уют\"")],
#     [InlineKeyboardButton("🏨 В ↘️ отель 'Ибис-Домодедово'", callback_data="point_отель \"Ибис-Домодедово\"")],
#     [InlineKeyboardButton("🏨 В ↘️ отель 'Виктория (Тюмень)'", callback_data="point_отель \"Виктория (Тюмень)\"")]
#     ]

POINTS_KEYBOARD_FROM = [
    [InlineKeyboardButton("🚀 ОТПРАВЛЕНИЕ: ✈️ а/п Шереметьево", callback_data="point_а/п Шереметьево")],
    [InlineKeyboardButton("🚀 ОТПРАВЛЕНИЕ: ✈️ а/п Домодедово", callback_data="point_а/п Домодедово")],
    [InlineKeyboardButton("🚀 ОТПРАВЛЕНИЕ: ✈️ а/п Внуково", callback_data="point_а/п Внуково")],
    [InlineKeyboardButton("🚀 ОТПРАВЛЕНИЕ: ✈️ а/п Рощино", callback_data="point_а/п Рощино")],
    [InlineKeyboardButton("🚀 ОТПРАВЛЕНИЕ: 🚇 ст.м. Домодедовская", callback_data="point_ст.м. Домодедовская")],
    [InlineKeyboardButton("🚀 ОТПРАВЛЕНИЕ: 🚇 ст.м. Ховрино", callback_data="point_ст.м. Ховрино")],
    [InlineKeyboardButton("🚀 ОТПРАВЛЕНИЕ: 🚂 ж/д Павелецкий", callback_data="point_ж/д Павелецкий")],
    [InlineKeyboardButton("🚀 ОТПРАВЛЕНИЕ: 🚂 ж/д Восточный", callback_data="point_ж/д Восточный")],
    [InlineKeyboardButton("🚀 ОТПРАВЛЕНИЕ: 🚂 ж/д Три вокзала", callback_data="point_ж/д Три вокзала")],
    [InlineKeyboardButton("🚀 ОТПРАВЛЕНИЕ: 🚂 ж/д Курский", callback_data="point_ж/д Курский")],
    [InlineKeyboardButton("🚀 ОТПРАВЛЕНИЕ: 🚂 ж/д Тюмень", callback_data="point_ж/д Тюмень")],
    [InlineKeyboardButton("🚀 ОТПРАВЛЕНИЕ: 🏨 отель 'Салют'", callback_data="point_отель \"Салют\"")],
    [InlineKeyboardButton("🚀 ОТПРАВЛЕНИЕ: 🏨 отель 'Уют'", callback_data="point_отель \"Уют\"")],
    [InlineKeyboardButton("🚀 ОТПРАВЛЕНИЕ: 🏨 отель 'Ибис-Домодедово'", callback_data="point_отель \"Ибис-Домодедово\"")],
    [InlineKeyboardButton("🚀 ОТПРАВЛЕНИЕ: 🏨 отель 'Виктория (Тюмень)'", callback_data="point_отель \"Виктория (Тюмень)\"")]
    ]

POINTS_KEYBOARD_TO = [
    [InlineKeyboardButton("🎯 НАЗНАЧЕНИЕ: ✈️ а/п Шереметьево", callback_data="point_а/п Шереметьево")],
    [InlineKeyboardButton("🎯 НАЗНАЧЕНИЕ: ✈️ а/п Домодедово", callback_data="point_а/п Домодедово")],
    [InlineKeyboardButton("🎯 НАЗНАЧЕНИЕ: ✈️ а/п Внуково", callback_data="point_а/п Внуково")],
    [InlineKeyboardButton("🎯 НАЗНАЧЕНИЕ: ✈️ а/п Рощино", callback_data="point_а/п Рощино")],
    [InlineKeyboardButton("🎯 НАЗНАЧЕНИЕ: 🚇 ст.м. Домодедовская", callback_data="point_ст.м. Домодедовская")],
    [InlineKeyboardButton("🎯 НАЗНАЧЕНИЕ: 🚇 ст.м. Ховрино", callback_data="point_ст.м. Ховрино")],
    [InlineKeyboardButton("🎯 НАЗНАЧЕНИЕ: 🚂 ж/д Павелецкий", callback_data="point_ж/д Павелецкий")],
    [InlineKeyboardButton("🎯 НАЗНАЧЕНИЕ: 🚂 ж/д Восточный", callback_data="point_ж/д Восточный")],
    [InlineKeyboardButton("🎯 НАЗНАЧЕНИЕ: 🚂 ж/д Три вокзала", callback_data="point_ж/д Три вокзала")],
    [InlineKeyboardButton("🎯 НАЗНАЧЕНИЕ: 🚂 ж/д Курский", callback_data="point_ж/д Курский")],
    [InlineKeyboardButton("🎯 НАЗНАЧЕНИЕ: 🚂 ж/д Тюмень", callback_data="point_ж/д Тюмень")],
    [InlineKeyboardButton("🎯 НАЗНАЧЕНИЕ: 🏨 отель 'Салют'", callback_data="point_отель \"Салют\"")],
    [InlineKeyboardButton("🎯 НАЗНАЧЕНИЕ: 🏨 отель 'Уют'", callback_data="point_отель \"Уют\"")],
    [InlineKeyboardButton("🎯 НАЗНАЧЕНИЕ: 🏨 отель 'Ибис-Домодедово'", callback_data="point_отель \"Ибис-Домодедово\"")],
    [InlineKeyboardButton("🎯 НАЗНАЧЕНИЕ: 🏨 отель 'Виктория (Тюмень)'", callback_data="point_отель \"Виктория (Тюмень)\"")]
    ]


# === ХЕЛПЕРЫ ДЛЯ БД И ДИРЕКТОРИИ ===
def ensure_data_dir():
    base_dir = Path(__file__).parent
    data_dir = base_dir / 'data'
    data_dir.mkdir(exist_ok=True)
    return str(data_dir / 'travel_bot.db')

def init_db():
    db_path = ensure_data_dir()
    conn = sqlite3.connect(db_path, timeout=20)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS travel_requests (
            request_id TEXT PRIMARY KEY,
            user_id INTEGER,
            contact_id TEXT,     -- username или телефон
            contact_type TEXT,   -- 'username' или 'phone'
            date TEXT,
            time TEXT,
            pass_qnt INTEGER,
            user_comment TEXT,
            departure_point TEXT,
            destination_point TEXT,
            time_window INTEGER,
            active INTEGER DEFAULT 1,
            delete_reason TEXT DEFAULT NULL,
            created_at TEXT,
            updated_at TEXT
        )
    ''')
    conn.commit()
    conn.close()

# === МОДЕЛЬ ЗАЯВКИ ===
class TravelRequest:
    def __init__(self, user_id, contact_id, contact_type):
        self.user_id = user_id
        self.contact_id = contact_id
        self.contact_type = contact_type
        self.date = None
        self.time = None
        self.pass_qnt = None
        self.user_comment = None
        self.departure_point = None
        self.destination_point = None
        self.time_window = None
        self.active = True
        self.request_id = datetime.now().strftime("%Y%m%d%H%M%S%f")
        self.created_at = datetime.now().isoformat()
        self.updated_at = None
        self.delete_reason = None

    def __str__(self):
        who = f"@{self.contact_id}" if self.contact_type == "username" else f"📞 {self.contact_id}"
        return (
            f"Запрос от {who} (ID: {self.request_id[-8:]})\n"
            f"Количество пассажиров: {self.pass_qnt}\n"
            f"Дата: {self.date.strftime('%d.%m.%Y')}\n"
            f"Время: {self.time}\n"
            f"Маршрут: {self.departure_point} → {self.destination_point}\n"
            f"Окно поиска: +{self.time_window} мин\n"
            f"Комментарий пользователя: {self.user_comment}"
        )

    def save(self):
        db_path = ensure_data_dir()
        conn = sqlite3.connect(db_path, timeout=20)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO travel_requests
            (request_id, user_id, contact_id, contact_type, date, time, pass_qnt,
            user_comment, departure_point, destination_point, time_window,
             active, delete_reason, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            self.request_id,
            self.user_id,
            self.contact_id,
            self.contact_type,
            str(self.date),
            str(self.time),
            self.pass_qnt,
            self.user_comment,
            self.departure_point,
            self.destination_point,
            self.time_window,
            1 if self.active else 0,
            self.delete_reason,
            self.created_at,
            datetime.now().isoformat()
        ))
        conn.commit()
        conn.close()

    @classmethod
    def get_active_requests(cls, user_id: Optional[int] = None):
        db_path = ensure_data_dir()
        conn = sqlite3.connect(db_path, timeout=20)
        cursor = conn.cursor()
        if user_id:
            cursor.execute('''
                SELECT * FROM travel_requests
                WHERE user_id = ? AND active = 1
                ORDER BY created_at DESC
            ''', (user_id,))
        else:
            cursor.execute('''
                SELECT * FROM travel_requests
                WHERE active = 1
                ORDER BY created_at DESC
            ''')
        results = []
        for row in cursor.fetchall():
            req = cls(row[1], row[2], row[3])
            req.request_id = row[0]
            req.date = datetime.strptime(row[4], '%Y-%m-%d').date()
            req.time = datetime.strptime(row[5], '%H:%M:%S').time()
            req.pass_qnt = row[6]
            req.user_comment = row[7]
            req.departure_point = row[8]
            req.destination_point = row[9]
            req.time_window = row[10]
            req.active = bool(row[11])
            req.delete_reason = row[12]
            req.created_at = row[13]
            req.updated_at = row[14]
            results.append(req)
        conn.close()
        return results

    @classmethod
    def get_by_short_id(cls, short_id: str, user_id: int):
        db_path = ensure_data_dir()
        conn = sqlite3.connect(db_path, timeout=20)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM travel_requests
            WHERE request_id LIKE ? AND user_id = ? AND active = 1
        ''', (f'%{short_id}', user_id))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return None
        req = cls(row[1], row[2], row[3])
        req.request_id = row[0]
        req.date = datetime.strptime(row[4], '%Y-%m-%d').date()
        req.time = datetime.strptime(row[5], '%H:%M:%S').time()
        req.pass_qnt = row[6]
        req.user_comment = row[7]
        req.departure_point = row[8]
        req.destination_point = row[9]
        req.time_window = row[10]
        req.active = bool(row[11])
        req.delete_reason = row[12]
        req.created_at = row[13]
        req.updated_at = row[14]
        conn.close()
        return req

    @classmethod
    def get_by_id(cls, request_id: str):
        db_path = ensure_data_dir()
        conn = sqlite3.connect(db_path, timeout=20)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM travel_requests WHERE request_id = ?', (request_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return None
        req = cls(row[1], row[2], row[3])
        req.request_id = row[0]
        req.date = datetime.strptime(row[4], '%Y-%m-%d').date()
        req.time = datetime.strptime(row[5], '%H:%M:%S').time()
        req.pass_qnt = row[6]
        req.user_comment = row[7]
        req.departure_point = row[8]
        req.destination_point = row[9]
        req.time_window = row[10]
        req.active = bool(row[11])
        req.delete_reason = row[12]
        req.created_at = row[13]
        req.updated_at = row[14]
        conn.close()
        return req

    def deactivate(self, reason: str = None):
        self.active = False
        self.delete_reason = reason
        self.updated_at = datetime.now().isoformat()
        self.save()
        return True

# === Проверка структуры БД ===
def check_db_structure():
    """Проверяет и обновляет структуру БД"""
    try:
        db_path = ensure_data_dir()
        conn = sqlite3.connect(db_path, timeout=20)
        cursor = conn.cursor()
        
        cursor.execute("PRAGMA table_info(travel_requests)")
        columns = {col[1]: col[2] for col in cursor.fetchall()}
        
        required_columns = {
            'request_id': 'TEXT',
            'user_id': 'INTEGER',
            'contact_id': 'TEXT',
            'contact_type': 'TEXT',
            'date': 'TEXT',
            'time': 'TEXT',
            'pass_qnt': 'INTEGER',
            'user_comment': 'TEXT',
            'departure_point': 'TEXT',
            'destination_point': 'TEXT',
            'time_window': 'INTEGER',
            'active': 'INTEGER',
            'delete_reason': 'TEXT',
            'created_at': 'TEXT',
            'updated_at': 'TEXT'
        }
        
        for col, col_type in required_columns.items():
            if col not in columns:
                cursor.execute(f"ALTER TABLE travel_requests ADD COLUMN {col} {col_type}")
                logger.info(f"Добавлена колонка: {col} {col_type}")
        
        conn.commit()
    except Exception as e:
        logger.error(f"Ошибка проверки структуры БД: {e}")
        raise
    finally:
        if conn:
            conn.close()
            
            
# === СПЕЦИАЛЬНОЕ МЕНЮ ДЛЯ ВСЕХ ===
MAIN_MENU = [
    ["🚕 Новая заявка"],
    ["📝 Мои заявки", "❌ Удалить заявку"],
    ["Стартовое меню, правовая и контактная информация"]  
]
def main_keyboard():
    return ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)


# === ОБРАБОТКА СВЯЗАННАЯ С СОГЛАШЕНИЕМ ===

# Ф-я формирования пути к БД соглашений
def get_consents_db_path():
    base_dir = Path(__file__).parent
    data_dir = base_dir / 'data'
    data_dir.mkdir(exist_ok=True)
    
    # print('get_consents_db_path')
    
    return str(data_dir / 'consents.db')

# Инициализация БД согласий
def init_consents_db():
    db_path = get_consents_db_path()
    conn = sqlite3.connect(db_path, timeout=20)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS consents (
            user_id INTEGER PRIMARY KEY,
            consented_at TEXT,
            user_name TEXT DEFAULT NULL,
            user_phone INTEGER DEFAULT NULL
        )
    ''')
    conn.commit()
    conn.close()
    
    # print('init_consents_db')

# Функция проверки согласия
def has_consented(user_id: int) -> bool:
    db_path = get_consents_db_path()
    conn = sqlite3.connect(db_path, timeout=20)
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM consents WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    
    # print('has_consented')
    
    
    return result is not None

# Функция сохранения согласия
def save_consent(user_id: int):
    db_path = get_consents_db_path()
    conn = sqlite3.connect(db_path, timeout=20)
    cursor = conn.cursor()
    cursor.execute(
        'INSERT OR IGNORE INTO consents (user_id, consented_at) VALUES (?, ?)',
        (user_id, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()
    

# Функция получения списка ID пользователей
def get_all_user_ids():
    db_path = get_consents_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT user_id FROM consents")
    ids_list = [row[0] for row in cursor.fetchall()]
    conn.close()
    return ids_list

# Сохранение юзернейма в БД согласий
async def save_user_name_to_consents(user_name: str, user_id: int):
    db_path = get_consents_db_path()
    conn = sqlite3.connect(db_path, timeout=20)
    cursor = conn.cursor()
    cursor.execute(
        'UPDATE consents SET user_name = ? WHERE user_id = ?',
        (user_name, user_id)
    )
    conn.commit()
    conn.close()
    
    # print('save_consent')

# Сохранения номера телефона пользователя в БД согласий
async def save_user_phone_to_consents(user_phone: int, user_id: int):
    db_path = get_consents_db_path()
    conn = sqlite3.connect(db_path, timeout=20)
    cursor = conn.cursor()
    cursor.execute(
        'UPDATE consents SET user_phone = ? WHERE user_id = ?',
        (user_phone, user_id)
    )
    conn.commit()
    conn.close()

# Запрос согласия пользователя 
async def validation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    
    user_id = update.effective_user.id
    
    if has_consented(user_id):
        # print('YEEEAH', user_id)
        await restart(update, context)
    else:
        print('ELSE IN VALIDATION')
        keyboard_agree = InlineKeyboardMarkup([
            [InlineKeyboardButton('Я согласен(-на) на обработку моих ПД и с правилами бота', callback_data='agree_personal_data')],
            [InlineKeyboardButton('Я НЕ согласен(-на)', callback_data='disagree_personal_data')]
        ])
        await update.message.reply_text(
            "Добро пожаловать в бот, который поможет Вам найти попутчика на такси.\n\n"
            "Данный сервис является некоммерческим.\n\n"
            "Функционал бота заключается в сборе заявок, где Вы укажете детали Вашей поездки."
            " Далее Вы и Ваши коллеги, в случае совпадения маршрутов, получат уведомления, "
            "которые содержат детали поездки и Ваши контактные данные (имя пользователя телеграмм"
            " или номер мобильного телефона при отсутствии имени пользователя).\n\n"
            "Данные операции подразумевают необходимость соблюдения 152-ФЗ 'О персональных данных'"
            " в его актуальной редакции.\n\n"
            " По следующим ссылкам Вы можете ознакомиться с Политикой обработки персоналных данных"
            " и правилами пользования данным ботом."
            "\nНажав кнопку <b>'Я согласен(-на) на обработку моих ПД и с правилами бота'</b>"
            " Вы <b>подтверждаете</b>, что:\n\n"
            "- <b>ознакомились и принимаете</b> представленную Политику обработки персоналных данных,"
            " <b>даёте своё согласие на обработку своих персональных данных</b> https://disk.yandex.ru/i/IRt-xqKvtK6FjA\n\n"
            "- <b>ознакомились</b> с представленными Правилами пользования сервисом данного телеграм-бота, <b>согласны</b> с ними,"
            " и <b>обязуетесь соблюдать</b> https://disk.yandex.ru/i/bvLYd2lmRYfezg"
            "\n\n В случае, если Вы не согласны, нажмите <b>'Я не согласен(-на)'</b>",
            parse_mode='HTML',
            reply_markup=keyboard_agree
            )
 
# Функция приветствия ПОСЛЕ согласия, запуск основного блока 
async def agree_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    save_consent(user_id)
    await query.answer()
    await query.edit_message_text("✅ Спасибо, вы согласились с Политикой обработки персональных данных, правилами телегарм-бота и дали своё согласие на обработку персональных данных.")
    
    # Теперь можно запускать основную логику (например, restart)
    await restart(update, context)        


async def disagree_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.edit_message_text("⛔ К сожалению, мы не сможем продолжить работу ⛔\n\n"
                                  "Вы не ознакомились с политикой обработки персональных данных и не дали"
                                  " согласия на обработку персональных данных. Это противоречит 152-ФЗ\n\n"
                                  "Ознакомиться и дать согласие: нажмите ➡️ /start")
    await ConversationHandler.END       
    


# === ХЕЛПЕРЫ ДЛЯ МАТЧЕЙ ===
def find_matches(request: TravelRequest) -> List[TravelRequest]:
    """Поиск совпадающих заявок с улучшенной логикой"""
    try:
        all_requests = TravelRequest.get_active_requests()
        matches = []
        
        request_datetime = datetime.combine(request.date, request.time)
        time_window = timedelta(minutes=request.time_window)
        
        for other_request in all_requests:
            if other_request.user_id == request.user_id:
                continue
                
            # Проверяем совпадение маршрута (прямое или обратное)
            route_match = (
                (other_request.departure_point == request.departure_point and
                 other_request.destination_point == request.destination_point) or
                (other_request.departure_point == request.destination_point and
                 other_request.destination_point == request.departure_point)
            )
            
            if not route_match:
                continue
                
            # Проверяем совпадение времени
            other_datetime = datetime.combine(other_request.date, other_request.time)
            time_diff = abs((request_datetime - other_datetime).total_seconds()) / 60  # в минутах
            
            if time_diff <= max(request.time_window, other_request.time_window):
                matches.append(other_request)
        
        return matches
    except Exception as e:
        logger.error(f"Ошибка поиска совпадений: {str(e)}")
        return []

async def notify_user_about_match(user_id: int, original_request: TravelRequest, match_request: TravelRequest, bot):
    """Уведомляет пользователя о новом совпадении"""
    text = (
        "🎉 Найден новый подходящий попутчик!\n\n"
        f"Для вашего запроса:\n{original_request}\n\n"
        f"Найден попутчик:\n"
        f"@{match_request.username}\n"
        f"Дата: {match_request.date}\n"
        f"Время: {match_request.time}\n"
        f"Направление: {match_request.direction}\n"
        f"💬 Комментарий: {match_request.user_comment}\n\n"
        "Используйте /delete_request чтобы удалить свой запрос после нахождения попутчика."
    )
    
    try:
        await bot.send_message(chat_id=user_id, text=text)
    except Exception as e:
        logger.error(f"Ошибка при отправке уведомления пользователю {user_id}: {e}")
    
    # В реальной реализации нужно отправить сообщение пользователю
    # await context.bot.send_message(chat_id=user_id, text=text, parse_mode=ParseMode.HTML)
    # print(f"Уведомление для пользователя {user_id}:\n{text}")  # Для демонстрации

async def notify_about_new_request(new_request: TravelRequest, bot):
    """Уведомление о новом запросе с улучшенной логикой"""
    try:
        matches = find_matches(new_request)
        if not matches:
            return
            
        for match in matches:
            try:
                # Определяем тип совпадения (прямое/обратное)
                if (match.departure_point == new_request.departure_point and
                    match.destination_point == new_request.destination_point):
                    match_type = "прямое направление"
                else:
                    match_type = "обратное направление"
                
                message = (
                    "🚖 Найден новый попутчик!\n\n"
                    f"📍 Ваш маршрут: {match.departure_point} → {match.destination_point}\n"
                    f"🔀 Совпадение: {match_type}\n"
                    f"👤 Пользователь: @{new_request.username}\n"
                    f"📅 Дата: {new_request.date.strftime('%d.%m.%Y')}\n"
                    f"⏰ Время: {new_request.time} (+ {new_request.time_window} мин)\n"
                    f"🙋‍♂️ Количество пассажиров: {new_request.pass_qnt}\n"
                    f"💬 Комментарий: {new_request.user_comment}\n\n"
                    "Напишите собеседнику для согласования деталей!"
                )
                
                await bot.send_message(
                    chat_id=match.user_id,
                    text=message,
                    parse_mode='HTML'
                )
            except Exception as e:
                logger.error(f"Ошибка уведомления пользователя {match.user_id}: {e}")
    except Exception as e:
        logger.error(f"Ошибка при поиске совпадений: {e}")

async def notify_about_matches(update: Update, context: CallbackContext, request: TravelRequest, matches: List[TravelRequest]):
    """Уведомляет пользователя о найденных совпадениях"""
    if not matches:
        return
    
    text = "🎉 Найдены подходящие попутчики:\n\n"
    for i, match in enumerate(matches, 1):
        text += (
            f"{i}. @{match.username}\n"
            f"Дата: {match.date}\n"
            f"Время: {match.time}\n"
            f"Направление: {match.direction}\n"
            f"🙋‍♂️ Количество пассажиров: {match.pass_qnt}\n"
            f"💬 Комментарий: {match.user_comment}\n\n"            
        )
    
    text += "Используйте /delete_request чтобы удалить свой запрос после нахождения попутчика."
    
    if update.callback_query:
        await update.callback_query.message.reply_text(text)
    else:
        await update.message.reply_text(text)


async def notify_about_match(user_id: int, original_request: TravelRequest, match_request: TravelRequest, bot):
    message = (
        "🚖 Найден попутчик!\n\n"
        f"📍 Ваш маршрут: {original_request.departure_point} → {original_request.destination_point}\n"
        f"👤 Попутчик: @{match_request.username}\n"
        f"🔄 Обратный маршрут: {match_request.destination_point} → {match_request.departure_point}\n"
        f"⏰ Время: {match_request.time}\n"
        f"📅 Дата: {match_request.date}\n"
        f"💬 Комментарий: {match_request.user_comment}\n\n"
        "Напишите собеседнику для согласования деталей"
    )
    await bot.send_message(chat_id=user_id, text=message)

# === ХЭНДЛЕРЫ СТАРТА И ПРОВЕРКИ КОНТАКТА ===

async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # print(black_list)
    try:
        
        # Проверка на наличия нахождения пользователя в диалоге (ошибочное нажатие гл.меню)
        if context.user_data.get('in_conversation'):

            await restart_and_end(update, context)
        
        # Если пользователь не в диалоге,просто запускается стартовое меню
        else:

    
            # Получение номера телефона из БД consents (если есть, если нет - None)
            user_id = update.effective_user.id
            
            if not has_consented(user_id):
                await update.message.reply_text(
                    "Вы не ознакомились с Политикой обработки персональных данных,"
                    " с Правилами пользования телеграмм-ботом,"
                    " а так же не дали свое согласие на обработку персональных данных\n\n"
                    "Ознакомиться и дать согласие ➡️ /start")
                return ConversationHandler.END
                
            if get_black_list_check(user_id):
                await update.message.reply_text(
                    "Вам ограничен доступ к использоваю чат-бота.\n\n"
                    "По возникшим вопросам свяжитесь, пожалуйста, по адресу taxicarpooling@mail.ru")
                return ConversationHandler.END
            
            db_path = get_consents_db_path()
            conn = sqlite3.connect(db_path, timeout=20)
            cursor = conn.cursor()
            cursor.execute(
                'SELECT user_phone FROM consents WHERE user_id = ?', (user_id,)
            )
            result = cursor.fetchone()
            conn.close()
            
            phone_number = result[0]
            
            # Выполнение основной логики функции
            
            # Подтягивания update в зависимости от того, каким образом зашел пользователь
            user = update.effective_user
            user_id = user.id
            username = user.username
            if update.message:
                reply = update.message.reply_text
            elif update.callback_query:
                reply = update.callback_query.message.reply_text
            else:
                # если совсем ничего нет, можно fallback:
                return
            
            # Проверка: если есть username — пропускаем дальше, иначе спрашиваем контакт
            if not username and not phone_number:
                # print('IF 1 RESTART')
                
                text = (
                    "❗️ У вас не установлен username в Telegram.\n"
                    "Вы можете создать его (это ваш Telegram-логин, например, @durov).\n\n"
                    "📝 <b>Как создать username?</b>\n"
                    "1. Зайдите в настройки Telegram.\n"
                    "2. Выберите «Имя пользователя»/«Username».\n"
                    "3. Придумайте себе уникальное имя (например, super_tg_user).\n\n"
                    "В случае затруднений, в данном вопросе, пожалуйста, воспользуйте поиском в интернете.\n\n"
                    "🔁ПОСЛЕ🔁 создания username, нажмите /start, чтобы начать пользоваться ботом.\n\n"
                    "↔️ИЛИ↔️ поделитесь своим номером телефона 🕻, если вы не хотите создавать username (нажмите кнопку в самом низу):"
                )
                button = ReplyKeyboardMarkup(
                    [[KeyboardButton("✅📲 Поделиться номером 📲✅", request_contact=True)]],
                    resize_keyboard=True, one_time_keyboard=True
                )
                await reply(text, parse_mode='HTML', reply_markup=button)
                return WAIT_PHONE
            
            # ЕСЛИ в качестве коммуникации является номер телефона
            if phone_number:
                
                context.user_data['contact_id'] = phone_number
                context.user_data['contact_type'] = 'phone'
                await reply(
                    f"👋 Привет, @{username}!\n"
                    "Я помогу тебе найти попутчиков для поездок.\n\n"
                    "📌 Доступные команды:\n"
                    "/new_request - создать новую заявку\n"
                    "/my_requests - мои заявки\n"
                    "/delete_request - удалить заявку\n\n"
                    "Чтобы начать, выберите команду или нижмите кнопку в меню ниже.\n\n"
                    "Меню бота - кнопка рядом с микрофоном (выглядит как квадратик, или как слэш /)\n\n"
                    "Дать обратную связь / сообщить о проблеме / отозвать согласие на обработку персональных данных @yuriy_ds7, taxicarpooling@mail.ru \n\n "
                    "Политика обработки персональных данных: https://disk.yandex.ru/i/IRt-xqKvtK6FjA.\n"
                    "Правила пользования сервисом данного телеграм-бота https://disk.yandex.ru/i/bvLYd2lmRYfezg",
                    parse_mode='HTML',
                    disable_web_page_preview=True,
                    reply_markup=main_keyboard()
                )
                
                return START
            
            # ЕСЛИ в качестве коммуникации является юзернейм
            else:
                
                context.user_data['contact_id'] = username
                context.user_data['contact_type'] = 'username'
                await reply(
                    f"👋 Привет, @{username}!\n"
                    "Я помогу тебе найти попутчиков для поездок.\n\n"
                    "📌 Доступные команды:\n"
                    "/new_request - создать новую заявку\n"
                    "/my_requests - мои заявки\n"
                    "/delete_request - удалить заявку\n\n"
                    "Чтобы начать, выберите команду или нижмите кнопку в меню ниже.\n\n"
                    "Меню бота - кнопка рядом с микрофоном (выглядит как квадратик, или как слэш /)\n\n"
                    "Дать обратную связь / сообщить о проблеме / отозвать согласие на обработку персональных данных @yuriy_ds7, taxicarpooling@mail.ru \n\n "
                    "Политика обработки персональных данных: https://disk.yandex.ru/i/IRt-xqKvtK6FjA.\n"
                    "Правила пользования сервисом данного телеграм-бота https://disk.yandex.ru/i/bvLYd2lmRYfezg",
                    parse_mode='HTML',
                    disable_web_page_preview=True,
                    reply_markup=main_keyboard()
                )
                await save_user_name_to_consents(username, user_id)
            
                return START
    except:
        pass

# Функция принудительно заверешения и перезапуска
async def restart_and_end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    
    cancel_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("↩️ Отменить составление заявки", callback_data="cancel_request")]
            ])
    await update.message.reply_text("❗Вы некорректно завершили оформление заявки❗\n\n" 
                                    "для завершения нажмите кнопку ниже\n"
                                    "⬇️⬇️ ⬇️⬇️ ⬇️⬇️",
                                    reply_markup=cancel_keyboard)
    await cancel(update, context)

# Функцяи запроса и сохранения номера
async def handle_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получаем телефон и сохраняем в user_data"""
    if update.message.contact and update.message.contact.phone_number:
        phone = update.message.contact.phone_number
        context.user_data['contact_id'] = phone
        context.user_data['contact_type'] = 'phone'
        user_id = update.effective_user.id
        await update.message.reply_text(
            "Спасибо! Ваш номер сохранён.\n"
            "Теперь вы можете пользоваться ботом для поиска попутчиков.\n\n"
            "Доступные команды:\n"
            "/new_request - создать новую заявку\n"
            "/my_requests - мои заявки\n"
            "/delete_request - удалить заявку\n"
            "Или, используйте кнопки внизу.",
            reply_markup=main_keyboard()
        )
        
        await save_user_phone_to_consents(phone, user_id)
        return START
    else:
        await update.message.reply_text(
            "Не удалось получить номер. Пожалуйста, нажмите кнопку «Поделиться номером» ниже.",
            reply_markup=ReplyKeyboardMarkup(
                [[KeyboardButton("Поделиться номером", request_contact=True)]],
                resize_keyboard=True, one_time_keyboard=True
            )
        )
        return WAIT_PHONE

# === СОЗДАНИЕ НОВОЙ ЗАЯВКИ ===

async def new_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:

    try:
        # Проверка на наличия нахождения пользователя в диалоге (ошибочное нажатие гл.меню)
        
        if context.user_data.get('in_conversation'):
        # if context.user_data:
        
            print('IN CONTEXT new_request', context.user_data)
            # ConversationHandler.END
            # await cancel(update, context)
            print(update)
            print(context)
            await restart_and_end(update, context)
        
        # Если пользователь не в диалоге,просто запускается стартовое меню
        else:    
            user_id = update.effective_user.id
            
            if not has_consented(user_id):
                await update.message.reply_text(
                    "Вы не ознакомились с Политикой обработки персональных данных,"
                    " с Правилами пользования телеграмм-ботом,"
                    " а так же не дали свое согласие на обработку персональных данных\n\n"
                    "Ознакомиться и дать согласие ➡️ /start")
                return ConversationHandler.END
                
                
            if get_black_list_check(user_id):
                await update.message.reply_text(
                    "Вам ограничен доступ к использованию телеграм-бота.\n\n"
                    "По возникшим вопросам свяжитесь, пожалуйста, по адресу taxicarpooling@mail.ru")
                return ConversationHandler.END
                
            if not context.user_data.get('contact_id'):
                # Защита от ручного ввода команды до прохождения restart
                await restart(update, context)
                
                # return WAIT_PHONE
                return ConversationHandler.END
            
            if context.user_data.get('in_conversation', False):
                await update.message.reply_text(
                    "У вас уже есть активный запрос. Завершите его или используйте /cancel.",
                    reply_markup=main_keyboard()
                )
                return ConversationHandler.END

    except:
        pass    
   
    context.user_data['in_conversation'] = True
    context.user_data['request'] = TravelRequest(
        update.effective_user.id,
        context.user_data['contact_id'],
        context.user_data['contact_type']
    )
    
    cancel_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(" ↩️ Отменить составление заявки", callback_data="cancel_request")]
        ])
    
    await update.message.reply_text(
        "Давайте создадим новую заявку!\n\n"
        "Введите дату поездки в формате <b>ДД.ММ.ГГГГ</b> (например, <b>02.07.2025</b>):\n\n",
        parse_mode='HTML',
        reply_markup=cancel_keyboard
    )
    return ENTER_DATE

async def enter_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if await handle_cancel(update, context): return ConversationHandler.END
    text = update.message.text
    text = text.replace('/', '.')
    text = text.replace(':', '.')
    try:
        date = datetime.strptime(text, "%d.%m.%Y").date()
        
        today_date = datetime.now().date()
        
        if date < today_date:
            cancel_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(" ↩️ Отменить составление заявки", callback_data="cancel_request")]
            ])
            await update.message.reply_text("Похоже, вы ищете попутчика в прошлом 🕰️.\nПопробуйте ввести дату еще раз.\n\n"
                                            "Или отмените составление заявки", 
                                            reply_markup=cancel_keyboard)
            return ENTER_DATE

        context.user_data['request'].date = date
        
        cancel_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(" ↩️ Отменить составление заявки", callback_data="cancel_request")]
        ])
                
        await update.message.reply_text(
            "Теперь введите желаемое время отправления (<b>ЧЧ:ММ</b>, например, <b>14:30</b>):\n\n",
            parse_mode='HTML',
            reply_markup=cancel_keyboard
        )
        return ENTER_TIME
    except ValueError:
        cancel_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(" ↩️ Отменить составление заявки", callback_data="cancel_request")]
        ])
        await update.message.reply_text("Неправильный формат даты. Попробуйте ещё раз.", 
                                        reply_markup=cancel_keyboard)
        return ENTER_DATE

async def enter_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if await handle_cancel(update, context): return ConversationHandler.END
    
    text = update.message.text
    text = text.replace('.', ':')
    text = text.replace('-', ':')
    text = text.replace('/', ':')
    
    try:
        time = datetime.strptime(text, "%H:%M").time()
        context.user_data['request'].time = time
        
        cancel_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(" ↩️ Отменить составление заявки", callback_data="cancel_request")]
        ])
              
        await update.message.reply_text(
            "👥 Укажите <b>количество</b> пассажиров:",
            parse_mode='HTML',
            reply_markup=cancel_keyboard
        )
        return ENTER_PASS_QNT
    
    except ValueError:
        cancel_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(" ↩️ Отменить составление заявки", callback_data="cancel_request")]
            ])
        await update.message.reply_text("Неправильный формат времени. Введите ЧЧ:ММ (например, 14:30):",
                                        reply_markup=cancel_keyboard)
        return ENTER_TIME

async def pass_qnt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if await handle_cancel(update, context): return ConversationHandler.END
    pass_quantity = update.message.text
    try:
        # time = datetime.strptime(text, "%H:%M").time()
        context.user_data['request'].pass_qnt = pass_quantity
        
        await update.message.reply_text(
            "💬 Напишите, пожалуйста, <b>важную информацию</b> о поездке, ее увидят Ваши"
            " потенциальные попутчики. Например, если у вас есть <b>багаж, сколько его, размер</b>.\n\n"
            "Если такой информации нет, отправьте в ответ прочерк",
            parse_mode='HTML'
            # reply_markup=InlineKeyboardMarkup(POINTS_KEYBOARD_FROM)
        )
        return ENTER_COMMENT
    except ValueError:
        cancel_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(" ↩️ Отменить составление заявки", callback_data="cancel_request")]
            ])
        await update.message.reply_text("Неправильный формат времени. Введите ЧЧ:ММ (например, 14:30):",
                                        reply_markup=cancel_keyboard)
        return ENTER_TIME

async def user_comment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if await handle_cancel(update, context): return ConversationHandler.END
    user_comment = update.message.text
    try:
        # time = datetime.strptime(text, "%H:%M").time()
        context.user_data['request'].user_comment = user_comment
        
        await update.message.reply_text(
            "📍 Укажите место отправления:",
            reply_markup=InlineKeyboardMarkup(POINTS_KEYBOARD_FROM)
        )
        return ENTER_DEPARTURE
    except ValueError:
        cancel_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(" ↩️ Отменить составление заявки", callback_data="cancel_request")]
            ])
        await update.message.reply_text("Неправильный формат времени. Введите ЧЧ:ММ (например, 14:30):",
                                        reply_markup=cancel_keyboard)
        return ENTER_TIME

async def enter_departure(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    selected_point = query.data.replace("point_", "")
    context.user_data['request'].departure_point = selected_point
    await query.edit_message_text(
        f"📍 Отправление: {selected_point}\n➡️ Теперь выберите место назначения:",
        reply_markup=InlineKeyboardMarkup(POINTS_KEYBOARD_TO)
    )
    return ENTER_DESTINATION

async def enter_destination(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    selected_point = query.data.replace("point_", "")
    context.user_data['request'].destination_point = selected_point
    
    cancel_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(" ↩️ Отменить составление заявки", callback_data="cancel_request")]
        ])
    
    await query.edit_message_text(
        "⌛ <b>Готовы подожать и увеличить шансы на поиск попутчиков?</b>\n\n"
        "Просто отправьте ответным сообщением количество <b>минут</b>, сколько готовы подождать (например, 30)\n\n",
        reply_markup=cancel_keyboard,
        parse_mode='HTML'
    )
    return ENTER_TIME_WINDOW

async def enter_time_window(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if await handle_cancel(update, context): return ConversationHandler.END
    try:
        time_window = int(update.message.text)
        if time_window <= 0: raise ValueError
        context.user_data['request'].time_window = time_window
        request = context.user_data['request']
        keyboard = [
            [InlineKeyboardButton("✅ Да", callback_data='confirm')],
            [InlineKeyboardButton("❌ Нет", callback_data='cancel')]
        ]
        await update.message.reply_text(
            f"Проверьте данные:\n{request}\n\nВсё верно?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return CONFIRM_REQUEST
    except ValueError:
        await update.message.reply_text("Введите положительное целое число (минуты):")
        return ENTER_TIME_WINDOW

async def confirm_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if query.data == 'confirm':
        request = context.user_data.get('request')
        try:
            request.save()
            response = (
                f"✅ <b>Заявка создана!</b>\n\n"
                f"{request}\n\n"
                f"🆔 ID заявки: <code>{request.request_id[-8:]}</code>\n\n"
                "❗️❗️❗️ Нашли попутчика/поменялись планы? Пожалуйста, удалите заявку через /delete_request\n\n"
                "Так Вы помогаете сохранять актуальную базу попутчиков и избавите Ваших коллег от долгого поиска."
            )
            matches = find_matches(request)
            if matches:
                response += "\n\n🎉 Найдены попутчики:\n"
                for m in matches:
                    who = f"@{m.contact_id}" if m.contact_type == "username" else f"📞 {m.contact_id}"
                    response += f"{who}\n{m.date.strftime('%d.%m.%Y')} {m.time}\n"
                    response += f"Количество пассажиров в заявке: {m.pass_qnt}\n"
                    response += f"Оставленный комментарий: {m.user_comment}\n\n"
                    
                    
                # Вызов функции уведомления пользователей, создавших заявки
                await notify_about_new_request(request, context.application.bot)
                
                response += "Пожалуйста, <b>самостоятельно</b> свяжитесть <b>с попутчиком</b> для обсуждения деталей."
                
            await query.edit_message_text(response, parse_mode='HTML')
        
        except Exception as e:
            logger.error(f"Ошибка сохранения заявки: {str(e)}")
            await query.edit_message_text("Ошибка при сохранении заявки.")
    else:
        await query.edit_message_text("Создание заявки отменено.\n Создать новую заявку? Жми ➡️ /new_request")
    
    for key in ['in_conversation', 'request', 'request_to_delete']:
        context.user_data.pop(key, None)
    # context.user_data.clear()
    return ConversationHandler.END

# === МОИ ЗАЯВКИ ===
async def my_requests(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    
    user_id = update.effective_user.id
    
    try:
        # Проверка на наличия нахождения пользователя в диалоге (ошибочное нажатие гл.меню)
        if not has_consented(user_id):
            await update.message.reply_text(
                "Вы не ознакомились с Политикой обработки персональных данных,"
                " с Правилами пользования телеграмм-ботом,"
                " а так же не дали свое согласие на обработку персональных данных\n\n"
                "Ознакомиться и дать согласие ➡️ /start")
            return ConversationHandler.END
            
        if get_black_list_check(user_id):
            await update.message.reply_text(
                "Вам ограничен доступ к использованию телеграм-бота.\n\n"
                "По возникшим вопросам свяжитесь, пожалуйста, по адресу taxicarpooling@mail.ru")
            return ConversationHandler.END   
             
        if context.user_data.get('in_conversation'):

            await restart_and_end(update, context)
        
        # Если пользователь не в диалоге,просто запускается стартовое меню
        else:

    
            user_id = update.effective_user.id
            requests = TravelRequest.get_active_requests(user_id)
            if not requests:
                await update.message.reply_text("У вас нет активных заявок. Создать заявку: /new_request", reply_markup=main_keyboard())
                # return START  #Тестово заблокировано
                return ConversationHandler.END
            text = "🚖 Ваши активные заявки:\n\n"
            for i, req in enumerate(requests, 1):
                who = f"@{req.contact_id}" if req.contact_type == "username" else f"📞 {req.contact_id}"
                text += (
                    f"{i}. {who}\n"
                    f"Маршрут: {req.departure_point} → {req.destination_point}\n"
                    f"Дата: {req.date.strftime('%d.%m.%Y')}\n"
                    f"Время: {req.time}\n"
                    f"Окно: +{req.time_window} мин\n"
                    f"Количество пассажиров в заявке: {req.pass_qnt}\n"
                    f"ID: <code>{req.request_id[-8:]}</code>\n\n"
                )
            await update.message.reply_text(text, parse_mode='HTML', reply_markup=main_keyboard())
            # return START
            return ConversationHandler.END
        
    except:
        pass


# === УДАЛЕНИЕ ЗАЯВКИ ===
async def delete_request_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    
    user_id = update.effective_user.id
    
    try:
        # Проверка на наличия нахождения пользователя в диалоге (ошибочное нажатие гл.меню)
        
        if context.user_data.get('in_conversation'):

            await restart_and_end(update, context)
        
        # Если пользователь не в диалоге,просто запускается стартовое меню
        else:
            
            if not has_consented(user_id):
                await update.message.reply_text(
                    "Вы не ознакомились с Политикой обработки персональных данных,"
                    " с Правилами пользования телеграмм-ботом,"
                    " а так же не дали свое согласие на обработку персональных данных\n\n"
                    "Ознакомиться и дать согласие ➡️ /start")
                return ConversationHandler.END
                
            if get_black_list_check(user_id):
                await update.message.reply_text(
                    "Вам ограничен доступ к использоваю чат-бота.\n\n"
                    "По возникшим вопросам свяжитесь, пожалуйста, по адресу taxicarpooling@mail.ru")
                return ConversationHandler.END
            # print('CATCH IN ELSE OF DELETE REQUEST START')
            
            user_id = update.effective_user.id
            requests = TravelRequest.get_active_requests(user_id)
            if not requests:
                await update.message.reply_text("У вас нет активных заявок для удаления.", reply_markup=main_keyboard())
                return ConversationHandler.END
            text = "Ваши активные заявки:\n\n"
            for req in requests:
                text += (
                    f"ID: <code>{req.request_id[-8:]}</code>\n"
                    f"Маршрут: {req.departure_point} → {req.destination_point}\n"
                    f"Дата: {req.date.strftime('%d.%m.%Y')} Время: {req.time}\n\n"
                    f"Количество пассажиров в заявке: {req.pass_qnt}\n"
                )
            await update.message.reply_text(
                text + "❓ Как удалить заявку \n"
                "Скопируйте ID заявки для удаления, нажав на номер, и отправьте этот номер:",
                parse_mode='HTML',
                reply_markup=main_keyboard()
            )
            return DELETE_REQUEST
        
    except:
        update.message.reply_text('⚠️ delete_request_start Произошла внутренняя ошибка, нажмите ➡️ /start')

async def delete_request_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    short_id = update.message.text.strip()
    user_id = update.effective_user.id
    request = TravelRequest.get_by_short_id(short_id, user_id)
    if not request:
        await update.message.reply_text(
            "❌ Не найдено активной заявки с таким ID. Проверьте через /my_requests.",
            reply_markup=main_keyboard()
        )
        return ConversationHandler.END
    context.user_data['request_to_delete'] = request
    keyboard = [
        [InlineKeyboardButton("✅ Попутчик найден", callback_data=f"delete_reason:found:{request.request_id}")],
        [InlineKeyboardButton("❌ Поездка не актуальна", callback_data=f"delete_reason:canceled:{request.request_id}")],
        [InlineKeyboardButton("🔙 Отменить", callback_data=f"delete_reason:abort:{request.request_id}")]
    ]
    await update.message.reply_text(
        f"Вы действительно хотите удалить заявку?\n"
        f"Маршрут: {request.departure_point} → {request.destination_point}\n"
        f"Дата: {request.date} Время: {request.time}\n"
        f"Количество пассажиров в заявке: {request.pass_qnt}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return DELETE_REASON

async def handle_delete_reason(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    _, reason, request_id = query.data.split(":")
    if reason == "abort":
        await query.edit_message_text("Удаление отменено.")
        # Чистим только FSM-флаги, контакт оставляем!
        for key in ['in_conversation', 'request', 'request_to_delete']:
            context.user_data.pop(key, None)
        return ConversationHandler.END
    request = TravelRequest.get_by_id(request_id)
    if not request:
        await query.edit_message_text("❌ Заявка не найдена.")
        for key in ['in_conversation', 'request', 'request_to_delete']:
            context.user_data.pop(key, None)
        return ConversationHandler.END
    reason_text = {"found": "Попутчик найден", "canceled": "Поездка отменена"}.get(reason, "Не указана")
    request.deactivate(reason_text)
    await query.edit_message_text(
        "Ваша заявка удалена. Спасибо, что помогаете поддерживать актуальную базу заявок.\n\n"
        f"✅ Заявка удалена\nПричина: {reason_text}\n\n"
        f"Маршрут: {request.departure_point} → {request.destination_point}\n"
        f"Дата: {request.date}\n"
        f"Время: {request.time}\n"
        f"Количество пассажиров в заявке: {request.pass_qnt}\n"
        f"Оставленный комментарий: {request.user_comment}\n\n",
    )
    await query.message.reply_text(
        "Для продолжения выберите действие в меню:",
        reply_markup=main_keyboard()
    )
    # ОЧИЩАЕМ ТОЛЬКО FSM!
    for key in ['in_conversation', 'request', 'request_to_delete']:
        context.user_data.pop(key, None)
    return ConversationHandler.END

# === ОБРАБОТЧИКИ ОТМЕНЫ И ОШИБОК ===

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:

    context.user_data['in_conversation'] = False
    context.user_data.pop('request', None)
    
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("Составление заявки прервано.\nНачать заново? Жми ➡️ /new_request")
    else:
        await update.message.reply_text("")
            
    return ConversationHandler.END


async def handle_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if update.message.text.lower() in ['отмена', 'cancel', '/cancel']:
        await cancel(update, context)
        return True
    return False


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Ошибка: {context.error}")
    try:
        if update and hasattr(update, 'message') and update.message:
            await update.message.reply_text("⚠️ Произошла внутренняя ошибка. Попробуйте позже.\n\n"
                                            "В случае <b>невозможности</b> перезапуска, напишите taxicarpooling@mail.ru",
                                            parse_mode='HTML')
    except Exception as e:
        logger.error(f"Ошибка в error_handler: {e}")


async def notify_about_new_request(new_request: TravelRequest, bot):
    matches = find_matches(new_request)
    for match in matches:
        try:
            # Не отправляем самому себе
            if match.user_id == new_request.user_id:
                continue
            who = f"@{new_request.contact_id}" if new_request.contact_type == "username" else f"📞 {new_request.contact_id}"
            await bot.send_message(
                chat_id=match.user_id,
                text=(
                    "🚖 Найден новый попутчик!\n\n"
                    f"Ваш маршрут: {match.departure_point} → {match.destination_point}\n"
                    f"Попутчик: {who}\n"
                    f"Дата: {new_request.date.strftime('%d.%m.%Y')}\n"
                    f"Время: {new_request.time} (+ готов ждать {new_request.time_window} мин)\n\n"
                    f"Количество пассажиров в заявке: {new_request.pass_qnt}\n"
                    f"Комментарий пассажира: {new_request.user_comment}\n\n"
                    "Пожалуйста, <b>самостоятельно</b> свяжитесь <b>с попутчиком</b> для согласования деталей."
                ),
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления попутчику: {e}")

# ===== РАССЫЛКА СООБЩЕНИЙ ПОЛЬЗОВАТЕЛЯМ  =====
async def announcement_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        gen_path = Path(__file__).parent
        # print('GEN PATH: ', gen_path)
        admin_list_path = gen_path / 'data'
        admin_list_path = admin_list_path / 'admin_list.txt'

        # print('BL PATH: ', black_list_path)
        with open(admin_list_path, 'r', encoding='utf-8') as file:
            data = file.read()
            ADMIN_IDS = ast.literal_eval(data)
    
        if update.effective_user.id not in ADMIN_IDS:
            await update.message.reply_text("⛔️ У вас нет доступа.")
            return ConversationHandler.END
        await update.message.reply_text("Введите текст объявления, которое хотите разослать:")
        return ANNOUNCEMENT_SEND
    
    except:
        await update.message.reply_text("Что-то пошло не так, возможно, Вам не хватает доступа или произошли какие-то проблемы.")
        return ConversationHandler.END
        

async def announcement_send(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    # Получи все user_id из твоей БД. Например:
    user_ids = get_all_user_ids()  # твоя функция!
    user_ids=list(set(user_ids))
    # Расчет задержки для отправки сообщений (защита от flood_limit)
    delay = min(max(0.0015 * len(user_ids), 0.05), 0.25)
    
    count, fail = 0, 0
    fail_list = list()
    for uid in user_ids:
        try:
            print('TRY')
            
            await context.bot.send_message(uid, text)
            count += 1
            await asyncio.sleep(delay)  # чтоб не словить flood_limit!
        except Exception as e:
            # print('EXCEPTION', repr(e))
            fail += 1
            fail_list.append((uid, e))
    await update.message.reply_text(f"✅ Сообщение отправлено {count} пользователям. Не доставлено: {fail} Список: {fail_list}")
    return ConversationHandler.END




def main() -> None:
    
    """Запуск бота"""
 
    try:
        # Инициализация БД
        init_db()
        try:
            check_db_structure()  # Проверяем и обновляем структуру
        except Exception as e:
            logger.error(f"Ошибка при проверке структуры БД: {e}")
        # check_db_structure()
        
        application = Application.builder().token(TG_TOKEN).build()
        
        application.add_handler(MessageHandler(filters.CONTACT, handle_phone))
        application.add_handler(CommandHandler('start', validation))
        application.add_handler(CallbackQueryHandler(agree_callback, pattern='^agree_personal_data$'))
        application.add_handler(CallbackQueryHandler(disagree_callback, pattern='^disagree_personal_data$'))
        
        application.add_handler(CommandHandler('my_requests', my_requests))
        application.add_handler(MessageHandler(filters.Regex("^📝 Мои заявки$"), my_requests))
        
        
        # Обработчики команды старт
        # application.add_handler(CommandHandler('перезапуск', restart))
        application.add_handler(MessageHandler(filters.Regex("^Стартовое меню, правовая и контактная информация$"), restart))
        # application.add_handler(MessageHandler(filters.Regex("^Мои заявки$"), restart))
        # application.add_handler(MessageHandler(filters.Regex("^Удалить заявку$"), restart))
        # application.add_handler(MessageHandler(filters.Regex("^Новая заявка$"), restart))
        

                
        # Обработчик создания заявки
        request_conv_handler = ConversationHandler(
            entry_points=[CommandHandler('new_request', new_request),
                          MessageHandler(filters.Regex("^🚕 Новая заявка$"), new_request)],
            states={
                ENTER_DATE: [MessageHandler(filters.Regex("^Стартовое меню, правовая и контактная информация$"), restart_and_end),
                              MessageHandler(filters.Regex("^Мои заявки$"), restart_and_end),
                              MessageHandler(filters.Regex("^Удалить заявку$"), restart_and_end),
                              CallbackQueryHandler(restart_and_end, pattern='^Удалить заявку$'),
                              MessageHandler(filters.Regex("^Новая заявка$"), restart_and_end),
                            MessageHandler(filters.TEXT & ~filters.COMMAND, enter_date)],
                ENTER_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_time)],
                ENTER_PASS_QNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, pass_qnt)],
                ENTER_COMMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, user_comment)],
                
                ENTER_DEPARTURE: [CallbackQueryHandler(enter_departure, pattern='^point_')],
                ENTER_DESTINATION: [CallbackQueryHandler(enter_destination, pattern='^point_')],    
                ENTER_TIME_WINDOW: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_time_window)],
                CONFIRM_REQUEST: [CallbackQueryHandler(confirm_request)],
                },
            fallbacks=[CommandHandler('cancel', cancel), 
                       CallbackQueryHandler(cancel, pattern='^cancel_request$'),
                       ],
            )
        
        application.add_handler(request_conv_handler)
        
        # Обработчик удаления заявки
        delete_conv_handler = ConversationHandler(
            entry_points=[CommandHandler('delete_request', delete_request_start),
                          MessageHandler(filters.Regex("^❌ Удалить заявку$"), delete_request_start)],
            states={
                DELETE_REQUEST: [#MessageHandler(filters.Regex("^Стартовое меню, правовая и контактная информация$"), cancel),
                                 MessageHandler(filters.TEXT & ~filters.COMMAND, delete_request_confirm)],
                DELETE_REASON: [CallbackQueryHandler(handle_delete_reason, pattern='^delete_reason:')],
            },
            fallbacks=[CommandHandler('cancel', cancel)],
        )
        application.add_handler(delete_conv_handler)
        
        tell_to_all_cond_handler = ConversationHandler(
            entry_points=[MessageHandler(filters.Regex(r"(?i)^сделать\s+объявление$"), announcement_start),
                          CommandHandler('tell_to_all', announcement_start)],
            
            states={
                # ANNOUNCEMENT_START: [MessageHandler(filters.TEXT & ~filters.COMMAND, announcement_start)],
                ANNOUNCEMENT_SEND: [MessageHandler(filters.TEXT & ~filters.COMMAND, announcement_send)]
                },
            fallbacks=[CommandHandler('cancel', cancel), 
                CallbackQueryHandler(cancel, pattern='^cancel_request$'),
                ]
            )
        
        application.add_handler(tell_to_all_cond_handler)
        
        
        # Обработчик ошибок
        application.add_error_handler(error_handler)
        
        logger.info("Бот запущен")
        application.run_polling()
        
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}", exc_info=True)
    finally:
        logger.info("Бот остановлен")
      

if __name__ == '__main__':
    
    init_db()
    init_consents_db()
    
    if check_db_structure():
        logger.info("Проверка целостности БД успешна")
    else:
        logger.warning("Обнаружены проблемы с БД, выполняется восстановление...")
    # print('hello')
    
    main()
