import asyncio
import time
import sqlite3
import random
import html 
import uuid
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command, CommandObject, StateFilter, or_f
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.enums import ParseMode
from aiogram.types import ReplyParameters
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData

# --- НАСТРОЙКИ ---
API_TOKEN = '8323682782:AAEKBtRbmWilweUrsJk4gC0ZmaqLS9RMR7U'
ADMINS = [6625239442, 7652697216, 8379042829, 674566914, 789277820]

# --- РОЛИ ДЛЯ ПРОФИЛЯ ---
ROLES = {
    6625239442: '<tg-emoji emoji-id="5156877291397055163">👑</tg-emoji> <b>Владелец</b>',
    7652697216: '<tg-emoji emoji-id="5438496463044752972">⭐️</tg-emoji> <b>Разработчик</b>',
    674566914: '<tg-emoji emoji-id="5438496463044752972">⭐️</tg-emoji> <b>Администратор бота</b>',
    789277820: '<tg-emoji emoji-id="5438496463044752972">⭐️</tg-emoji> <b>Администратор бота</b>'
}

# --- ЭМОДЗИ (КАРТОЧКИ И БАЗА) ---
E_LINE = '<tg-emoji emoji-id="5467751241939429038">🟧</tg-emoji>'
E_WELCOME_WINGS = '<tg-emoji emoji-id="5064709487953183440">⭐️</tg-emoji>'
E_FINANCE = '<tg-emoji emoji-id="5019626126780138240">💼</tg-emoji>'
E_SUITCASE = '<tg-emoji emoji-id="5445221832074483553">💼</tg-emoji>'
E_BASIC = '<tg-emoji emoji-id="5400289821253990206">📜</tg-emoji>'
E_BONUS = '<tg-emoji emoji-id="5463325187946597693">🎁</tg-emoji>'
E_PLAYER = '<tg-emoji emoji-id="5353015915090811666">👤</tg-emoji>'
E_TG_ID = '<tg-emoji emoji-id="5936017305585586269">🆔</tg-emoji>'
E_COINS = '<tg-emoji emoji-id="5409048419211682843">💵</tg-emoji>'
E_BOX = '<tg-emoji emoji-id="5463325187946597693">📦</tg-emoji>' # Эмодзи донат валюты
E_SERIES = '<tg-emoji emoji-id="5463292486065616366">🔥</tg-emoji>'
E_CARD_STAR = '<tg-emoji emoji-id="5222224600330419057">⭐️</tg-emoji>'
E_TIME_STAR = '<tg-emoji emoji-id="5463064646640495858">⭐️</tg-emoji>'
E_LEGEND_STAR = '<tg-emoji emoji-id="5170574646478635764">⭐️</tg-emoji>'

E_REWARD_STAR = '<tg-emoji emoji-id="5330194932781050507">🌟</tg-emoji>'
E_TOP_1 = '<tg-emoji emoji-id="5399852280050646232">🏆</tg-emoji>'

# --- ЭМОДЗИ (ДЛЯ ЕЖЕДНЕВКИ) ---
E_DAILY_MAIN = '<tg-emoji emoji-id="5064709487953183440">⭐️</tg-emoji>'
E_DAILY_RECEIVED = '<tg-emoji emoji-id="5019626126780138240">⭐️</tg-emoji>'
E_DAILY_BASE = '<tg-emoji emoji-id="5400289821253990206">⭐️</tg-emoji>'
E_DAILY_BONUS = '<tg-emoji emoji-id="5463325187946597693">⭐️</tg-emoji>'
E_DAILY_SERIES = '<tg-emoji emoji-id="5463292486065616366">⭐️</tg-emoji>'

# --- ЭМОДЗИ (БРАК И СОЦИУМ) ---
E_PARTNER = '<tg-emoji emoji-id="5463195522883940716">❤️‍🔥</tg-emoji>'
E_START = '<tg-emoji emoji-id="5323711069762381423">🎁</tg-emoji>'
E_SUCCESS = '<tg-emoji emoji-id="5323568584222336801">🎁</tg-emoji>'
E_DAYS = '<tg-emoji emoji-id="5413879192267805083">🗓</tg-emoji>'
E_ALERT = '<tg-emoji emoji-id="5424818078833715060">📣</tg-emoji>'
E_STATS = '<tg-emoji emoji-id="5231200819986047254">📊</tg-emoji>'
E_OFFENDED = '<tg-emoji emoji-id="5463099040738600646">❌</tg-emoji>'
E_FORGIVEN = '<tg-emoji emoji-id="5206607081334906820">✔️</tg-emoji>'
E_HOUSE = '<tg-emoji emoji-id="5416041192905265756">🏠</tg-emoji>'

E_LINE_STR = E_LINE * 15

# Редкости карточек (base добавлен для кнопок)
RARITIES = {
    "Обычная": {"emoji": '<tg-emoji emoji-id="5350833530538583240">💎</tg-emoji>', "base": "💎", "chance": 70, "reward": (1, 30)},
    "Редкая": {"emoji": '<tg-emoji emoji-id="5348405014295506484">💎</tg-emoji>', "base": "💎", "chance": 20, "reward": (20, 45)},
    "Эпическая": {"emoji": '<tg-emoji emoji-id="5348569112110984279">💎</tg-emoji>', "base": "💎", "chance": 8, "reward": (40, 58)},
    "Легендарная": {"emoji": '<tg-emoji emoji-id="5348246727570780160">💎</tg-emoji>', "base": "💎", "chance": 2, "reward": (60, 140)},
    "Мифическая": {"emoji": '<tg-emoji emoji-id="5348092838892565131">💎</tg-emoji>', "base": "💎", "chance": 1, "reward": (70, 250)}
}

# --- ЭМОДЗИ ДЛЯ КРЕСТИКОВ-НОЛИКОВ ---
TTT_E_X = '<tg-emoji emoji-id="5348204890294350245">🫙</tg-emoji>'
TTT_E_O = '<tg-emoji emoji-id="5348219901205048470">🫙</tg-emoji>'
TTT_E_EMPTY = "⬜️"

# Глобальный словарь активных игр в крестики-нолики
active_ttt_games = {}

# --- БД (SQLite) ---
conn = sqlite3.connect('hakka_full.db', check_same_thread=False)
cursor = conn.cursor()

def db_init():
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY, coins INTEGER DEFAULT 0, series INTEGER DEFAULT 0, 
        last_daily TEXT, last_card_time REAL DEFAULT 0, gender TEXT)''')
    
    # Добавляем юзернейм и донат-валюту box
    try: cursor.execute("ALTER TABLE users ADD COLUMN username TEXT")
    except sqlite3.OperationalError: pass
    try: cursor.execute("ALTER TABLE users ADD COLUMN box INTEGER DEFAULT 0")
    except sqlite3.OperationalError: pass
        
    cursor.execute('''CREATE TABLE IF NOT EXISTS cards (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, rarity TEXT, photo_id TEXT, description TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS user_cards (
        user_id INTEGER, card_id INTEGER)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS marriages (
        chat_id INTEGER, user_id INTEGER, partner_id INTEGER, time REAL, 
        is_offended INTEGER DEFAULT 0, lvl INTEGER DEFAULT 1, exp INTEGER DEFAULT 0, house TEXT DEFAULT 'Нет дома',
        PRIMARY KEY(chat_id, user_id))''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS marriage_actions (
        id INTEGER PRIMARY KEY AUTOINCREMENT, action_type TEXT, template TEXT)''')
        
    cursor.execute('''CREATE TABLE IF NOT EXISTS rp_commands (
        command TEXT PRIMARY KEY, template TEXT, is_marriage INTEGER DEFAULT 0)''')
        
    # Предустановленные действия для брака
    cursor.execute("INSERT OR IGNORE INTO rp_commands (command, template, is_marriage) VALUES ('кусь', '<blockquote>{fam1} ласково кусает {fam2} <tg-emoji emoji-id=\"5364050751226127978\">🤪</tg-emoji></blockquote>', 1)")
    cursor.execute("INSERT OR IGNORE INTO rp_commands (command, template, is_marriage) VALUES ('обнять', '<blockquote>{fam1} крепко обнимает {fam2} ❤️</blockquote>', 1)")
    cursor.execute("INSERT OR IGNORE INTO rp_commands (command, template, is_marriage) VALUES ('поцеловать', '<blockquote>{fam1} нежно целует {fam2} 💋</blockquote>', 1)")
    conn.commit()

db_init()

def get_u(uid, username=None):
    cursor.execute("SELECT coins, series, last_daily, last_card_time, gender, box FROM users WHERE id=?", (uid,))
    res = cursor.fetchone()
    if not res:
        cursor.execute("INSERT INTO users (id, username, coins, series, box) VALUES (?, ?, 0, 0, 0)", (uid, username))
        conn.commit()
        return 0, 0, "", 0, None, 0
    if username:
        cursor.execute("UPDATE users SET username=? WHERE id=?", (username, uid))
        conn.commit()
    return res

# --- КОЛЛБЭКИ И СОСТОЯНИЯ ---
class AdminPanel(StatesGroup):
    cb_wait_photo = State()
    cb_wait_name = State()
    cb_wait_desc = State()
    cb_wait_rarity = State()
    rpg_wait_trigger = State()
    rpg_wait_template = State()
    rpg_wait_edit_template = State()
    m_wait_compliment = State()
    m_wait_gift = State()
    wait_give_coins = State()
    wait_give_lvl = State()

class MarriageAction(CallbackData, prefix="m"):
    a: str
    pid: int
    tid: int

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---
async def check_offend_status(message: types.Message, chat_id: int, user_id: int):
    cursor.execute("SELECT partner_id FROM marriages WHERE chat_id=? AND user_id=?", (chat_id, user_id))
    m = cursor.fetchone()
    if m:
        partner_id = m[0]
        cursor.execute("SELECT is_offended FROM marriages WHERE chat_id=? AND user_id=?", (chat_id, partner_id))
        p = cursor.fetchone()
        if p and p[0] == 1:
            await message.reply(f"{E_OFFENDED} <b>Действие заблокировано!</b>\nТвоя половинка обиделась на тебя. Пока она не простит (.хакка простить), действия недоступны!", parse_mode=ParseMode.HTML)
            return True
    return False

# --- 1. СТАРТ И ВЫБОР ПОЛА ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message, command: CommandObject):
    uid = message.from_user.id
    username = message.from_user.username
    c, s, _, _, gender, box = get_u(uid, username)
    
    if command.args and command.args.startswith("ref_"):
        ref_id = int(command.args.replace("ref_", ""))
        if ref_id != uid:
            cursor.execute("UPDATE users SET coins = coins + 50 WHERE id=?", (uid,))
            cursor.execute("UPDATE users SET coins = coins + 100 WHERE id=?", (ref_id,))
            conn.commit()
            try: await bot.send_message(ref_id, f"{E_COINS} <b>+100 монет!</b> По твоей ссылке зашел игрок.", parse_mode=ParseMode.HTML)
            except: pass

    if not gender:
        builder = InlineKeyboardBuilder()
        builder.button(text="👨 Мужской", callback_data="gender_m")
        builder.button(text="👩 Женский", callback_data="gender_f")
        return await message.reply(f"{E_START} <b>Добро пожаловать!</b> Выбери пол для профиля:", reply_markup=builder.as_markup(), parse_mode=ParseMode.HTML)

    welcome_text = (
        f"{E_WELCOME_WINGS} <b>Добро пожаловать в Hakка cards!</b> {E_WELCOME_WINGS}\n"
        f"<blockquote>Я помогаю собирать уникальные карты и строить семьи!</blockquote>\n\n"
        f"<b>Команды:</b>\n"
        f"<blockquote>/card — Получить карту\n"
        f"/mycards — Ваша коллекция\n"
        f"/top — Рейтинги игроков\n"
        f".хакка брак — Предложить брак (реплай)\n"
        f".хакка профиль — Статистика\n"
        f".хакка дома — Купить жилье\n"
        f"/donate — Купить Box валюту\n"
        f"/ttt — Играть в Крестики-Нолики\n"
        f"/man или /woman — Установить пол</blockquote>"
    )
    await message.answer(welcome_text, parse_mode=ParseMode.HTML)

@dp.callback_query(F.data.startswith("gender_"))
async def set_gender_cb(callback: types.CallbackQuery):
    g = "Мужской" if callback.data == "gender_m" else "Женский"
    cursor.execute("UPDATE users SET gender=? WHERE id=?", (g, callback.from_user.id))
    conn.commit()
    await callback.message.edit_text(f"{E_SUCCESS} Пол установлен: <b>{g}</b>! Напиши /start еще раз.", parse_mode=ParseMode.HTML)

@dp.message(Command("man"))
async def cmd_man(message: types.Message):
    get_u(message.from_user.id, message.from_user.username)
    cursor.execute("UPDATE users SET gender='Мужской' WHERE id=?", (message.from_user.id,))
    conn.commit()
    await message.reply(f"{E_SUCCESS} Ваш пол успешно изменен на <b>Мужской</b>!", parse_mode=ParseMode.HTML)

@dp.message(Command("woman"))
async def cmd_woman(message: types.Message):
    get_u(message.from_user.id, message.from_user.username)
    cursor.execute("UPDATE users SET gender='Женский' WHERE id=?", (message.from_user.id,))
    conn.commit()
    await message.reply(f"{E_SUCCESS} Ваш пол успешно изменен на <b>Женский</b>!", parse_mode=ParseMode.HTML)

@dp.message(Command("emojico"), F.from_user.id.in_(ADMINS))
async def cmd_emojico(message: types.Message):
    entities = message.entities or []
    codes = []
    for ent in entities:
        if ent.type == "custom_emoji":
            char = message.text[ent.offset : ent.offset + ent.length]
            codes.append(f'&lt;tg-emoji emoji-id="{ent.custom_emoji_id}"&gt;{char}&lt;/tg-emoji&gt;')
            
    if not codes:
        return await message.reply("❌ Премиум эмодзи не найдены.\nОтправь команду и нужные эмодзи в одном сообщении. Например:\n`/emojico 🌟🔥`", parse_mode=ParseMode.MARKDOWN)
        
    response = "<b>Вставь этот HTML код в скрипт:</b>\n\n" + "\n\n".join(f"<code>{c}</code>" for c in codes)
    await message.reply(response, parse_mode=ParseMode.HTML)

# --- ДОНАТ СИСТЕМА ---
@dp.message(Command("donate"))
async def cmd_donate(message: types.Message):
    text = (
        f"💎 <b>Покупка Донат Валюты (Box)</b>\n"
        f"{E_LINE_STR}\n"
        f"За валюту Box можно приобрести эксклюзивные кастомные дома и другие плюшки!\n\n"
        f"💵 <b>Прайс-лист:</b>\n"
        f"  ┝ 150₽ — 300 Box\n"
        f"  ┝ 300₽ — 600 Box\n"
        f"  ┕ 599₽ — 1200 Box\n\n"
        f"<i>Для покупки перейдите в нашего бота-кассира:</i>"
    )
    builder = InlineKeyboardBuilder()
    builder.button(text="💳 Купить Box", url="http://t.me/PayElhakkabot")
    await message.reply(text, reply_markup=builder.as_markup(), parse_mode=ParseMode.HTML)

# --- 2. ЕДИНЫЙ ПРОФИЛЬ ---
@dp.message(F.text.lower().in_({".хакка профиль", "профиль", "/profile"}))
async def cmd_profile(message: types.Message):
    uid = message.from_user.id
    chat_id = message.chat.id
    c, s, _, _, gender, box = get_u(uid, message.from_user.username)
    
    cursor.execute("SELECT partner_id, time, lvl, house FROM marriages WHERE chat_id=? AND user_id=?", (chat_id, uid))
    m = cursor.fetchone()
    
    status = "Одинок"
    house = "Нет дома"
    
    if m:
        p_id, m_time, m_lvl, m_house = m
        try:
            p_info = await bot.get_chat(p_id)
            p_name = p_info.first_name
        except:
            p_name = f"ID: {p_id}"
        days = int((time.time() - m_time) // 86400)
        status = f"{E_PARTNER} В браке с: {p_name}\n  ┝ {E_DAYS} Дней: {days}\n  ┕ {E_STATS} Lvl: {m_lvl}"
        house = m_house
        
        # Кастомная выдача домов для владельцев, если дом еще базовый
        if uid == 6625239442 and house == "Нет дома":
            house = '<tg-emoji emoji-id="5285322720790224022">😀</tg-emoji> Дом Императора'
            cursor.execute("UPDATE marriages SET house=? WHERE chat_id=? AND (user_id=? OR partner_id=?)", (house, chat_id, uid, uid))
            conn.commit()
        elif uid == 7652697216 and house == "Нет дома":
            house = '<tg-emoji emoji-id="5323276453431775004">🏰</tg-emoji> Особняк Hakka'
            cursor.execute("UPDATE marriages SET house=? WHERE chat_id=? AND (user_id=? OR partner_id=?)", (house, chat_id, uid, uid))
            conn.commit()

    user_status = ROLES.get(uid, f'{E_PLAYER} <b>Игрок</b>')
    photos = await bot.get_user_profile_photos(uid, limit=1)
    
    # ЛОГИКА ЗАМЕНЫ ЗВЕЗД ДЛЯ ВЛАДЕЛЬЦА
    if uid == 6625239442:
        title_emoji = '<tg-emoji emoji-id="5334617288807048693">🌟</tg-emoji>'
    else:
        title_emoji = E_WELCOME_WINGS

    text = (
        f"{title_emoji} <b>ПРОФИЛЬ ИГРОКА: {message.from_user.first_name}</b> {title_emoji}\n"
        f"{E_LINE_STR}\n\n"
        f'<tg-emoji emoji-id="5339511094803195372">🌟</tg-emoji> <b>Статус:</b> {user_status}\n'
        f"{E_PLAYER} <b>Имя:</b> {message.from_user.first_name}\n"
        f'<tg-emoji emoji-id="5377790574944361492">⚧️</tg-emoji> <b>Пол:</b> {gender or "Не указан"}\n'
        f"{E_TG_ID} <b>ID:</b> <code>{uid}</code>\n"
        f"{E_LINE_STR}\n\n"
        f"{E_FINANCE} <b>Финансы:</b>\n"
        f"  ┝ {E_COINS} Баланс: <b>{c}</b> Hacoins\n"
        f"  ┝ {E_BOX} Box: <b>{box}</b>\n"
        f"  ┕ {E_SERIES} Серия: <b>{s}</b> дней\n\n"
        f"{E_HOUSE} <b>Семья (в этом чате):</b>\n"
        f"  ┝ Дом: <b>{house}</b>\n"
        f"  ┕ {status}\n"
        f"{E_LINE_STR}"
    )
    
    if photos.total_count > 0:
        await message.answer_photo(photo=photos.photos[0][-1].file_id, caption=text, parse_mode=ParseMode.HTML)
    else:
        await message.reply(text, parse_mode=ParseMode.HTML)

# --- ТОП ИГРОКОВ ---
@dp.message(Command("top"))
async def cmd_top(message: types.Message):
    get_u(message.from_user.id, message.from_user.username)
    
    builder = InlineKeyboardBuilder()
    builder.button(text="🔥 Топ по Серии Дней", callback_data="top_series")
    builder.button(text="💵 Топ по HakkaCoins", callback_data="top_coins")
    builder.button(text="🎴 Топ по Картам", callback_data="top_cards")
    builder.adjust(1)
    
    await message.reply("🏆 <b>Выберите категорию топа:</b>", reply_markup=builder.as_markup(), parse_mode=ParseMode.HTML)

@dp.callback_query(F.data.startswith("top_"))
async def top_callbacks(callback: types.CallbackQuery):
    category = callback.data.split("_")[1]
    
    if category == "coins":
        cursor.execute("SELECT id, username, coins FROM users ORDER BY coins DESC LIMIT 10")
        data = cursor.fetchall()
        text = "🏆 <b>Топ по HakkaCoins:</b>\n\n"
        val_name = "Hacoins"
    elif category == "series":
        cursor.execute("SELECT id, username, series FROM users ORDER BY series DESC LIMIT 10")
        data = cursor.fetchall()
        text = "🏆 <b>Топ по Серии Дней:</b>\n\n"
        val_name = "дней"
    elif category == "cards":
        cursor.execute("""
            SELECT users.id, users.username, COUNT(user_cards.card_id) as c 
            FROM user_cards 
            JOIN users ON user_cards.user_id = users.id 
            GROUP BY users.id 
            ORDER BY c DESC LIMIT 10
        """)
        data = cursor.fetchall()
        text = "🏆 <b>Топ по собранным Картам:</b>\n\n"
        val_name = "карт"
        
    if not data:
        text += "Пока никого нет..."
    else:
        for i, row in enumerate(data):
            uid, uname, val = row
            name = f"@{uname}" if uname else f"ID: {uid}"
            
            if i == 0:
                rank_emoji = E_TOP_1
            elif i == 1: rank_emoji = "🥈"
            elif i == 2: rank_emoji = "🥉"
            else: rank_emoji = f"<b>{i+1}.</b>"
                
            text += f"{rank_emoji} {name} — {val} {val_name}\n"
            
    await callback.message.edit_text(text, reply_markup=callback.message.reply_markup, parse_mode=ParseMode.HTML)

# --- 3. БРАКИ И СЕМЬЯ ---
@dp.message(F.text.lower() == ".хакка брак")
async def start_marriage(message: types.Message):
    if not message.reply_to_message:
        return await message.reply("Чтобы предложить брак, ответь этой командой на сообщение игрока!")
    
    chat_id, p_id, t_id = message.chat.id, message.from_user.id, message.reply_to_message.from_user.id
    if p_id == t_id: return await message.reply("Нельзя жениться на себе!")
    
    cursor.execute("SELECT * FROM marriages WHERE chat_id=? AND user_id=?", (chat_id, p_id))
    if cursor.fetchone(): return await message.reply("У тебя уже есть брак в этом чате!")

    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Согласен", callback_data=MarriageAction(a="y", pid=p_id, tid=t_id).pack())
    builder.button(text="❌ Отказ", callback_data=MarriageAction(a="n", pid=p_id, tid=t_id).pack())
    
    await message.reply(f"{E_PARTNER} {message.from_user.first_name} предлагает брак {message.reply_to_message.from_user.first_name}!", 
                        reply_markup=builder.as_markup(), parse_mode=ParseMode.HTML)

@dp.callback_query(MarriageAction.filter())
async def process_marriage(callback: types.CallbackQuery, callback_data: MarriageAction):
    if callback.from_user.id != callback_data.tid: return await callback.answer("Это не тебе предложили!")
    
    if callback_data.a == "y":
        now = time.time()
        chat_id = callback.message.chat.id
        cursor.execute("INSERT INTO marriages (chat_id, user_id, partner_id, time) VALUES (?, ?, ?, ?)", (chat_id, callback_data.pid, callback_data.tid, now))
        cursor.execute("INSERT INTO marriages (chat_id, user_id, partner_id, time) VALUES (?, ?, ?, ?)", (chat_id, callback_data.tid, callback_data.pid, now))
        conn.commit()
        await callback.message.edit_text(f"{E_ALERT} {E_SUCCESS} <b>Поздравляем!</b> Теперь вы пара в этом чате!", parse_mode=ParseMode.HTML)
    else:
        await callback.message.edit_text(f"{E_ALERT} Пользователь отклонил предложение.", parse_mode=ParseMode.HTML)

# --- 4. СОЦИУМ (ОБИДЫ, ДОМА, ПОДАРКИ, КОМПЛИМЕНТЫ) ---
@dp.message(F.text.lower().in_({".хакка обидеться", ".хакка простить", ".хакка дома"}))
async def social_commands(message: types.Message):
    cmd = message.text.lower().replace(".хакка ", "").strip()
    chat_id, uid = message.chat.id

    if cmd != "простить" and await check_offend_status(message, chat_id, uid):
        return

    if cmd == "обидеться":
        cursor.execute("SELECT partner_id FROM marriages WHERE chat_id=? AND user_id=?", (chat_id, uid))
        m = cursor.fetchone()
        if not m: return await message.reply("У тебя нет пары в этом чате.")
        
        cursor.execute("UPDATE marriages SET is_offended=1 WHERE chat_id=? AND user_id=?", (chat_id, uid))
        conn.commit()
        try:
            p_info = await bot.get_chat(m[0])
            p_name = p_info.first_name
        except: p_name = "твою половинку"
        await message.reply(f"{E_OFFENDED} {message.from_user.first_name}, ты обиделся на {p_name}. Действия заблокированы!", parse_mode=ParseMode.HTML)

    elif cmd == "простить":
        cursor.execute("UPDATE marriages SET is_offended=0 WHERE chat_id=? AND user_id=?", (chat_id, uid))
        if cursor.rowcount > 0:
            conn.commit()
            await message.reply(f"{E_FORGIVEN} Поздравляю, твоя половинка больше не обижается, действия разблокированы!", parse_mode=ParseMode.HTML)

    elif cmd == "дома":
        cursor.execute("SELECT partner_id FROM marriages WHERE chat_id=? AND user_id=?", (chat_id, uid))
        m = cursor.fetchone()
        if not m:
            return await message.reply("🏠 <b>Дома могут приобретать только те, кто состоит в браке!</b>", parse_mode=ParseMode.HTML)
            
        builder = InlineKeyboardBuilder()
        builder.button(text="🏠 Лачуга (500 Hacoins)", callback_data="buyh_c_500_Лачуга")
        builder.button(text="🏡 Коттедж (1500 Hacoins)", callback_data="buyh_c_1500_Коттедж")
        builder.button(text="🏰 Замок (4000 Hacoins)", callback_data="buyh_c_4000_Замок")
        builder.button(text="🏠 Домик Hakka (99 Box)", callback_data="buyh_b_99_Домик Hakka")
        builder.button(text="🏰 Особняк Hakka (200 Box)", callback_data="buyh_b_200_Особняк Hakka")
        builder.button(text="😀 Дом Императора (400 Box)", callback_data="buyh_b_400_Дом Императора")
        builder.adjust(1)
        await message.reply(f"{E_HOUSE} <b>Выберите дом для семьи:</b>", reply_markup=builder.as_markup(), parse_mode=ParseMode.HTML)

@dp.callback_query(F.data.startswith("buyh_"))
async def buy_house(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    val_type = parts[1] # c - coins, b - box
    price = int(parts[2])
    h_name = parts[3]
    uid, chat_id = callback.from_user.id, callback.message.chat.id

    c, s, _, _, _, box = get_u(uid)
    
    if val_type == 'c':
        if c < price: return await callback.answer("Недостаточно Hacoins!", show_alert=True)
        cursor.execute("UPDATE users SET coins=coins-? WHERE id=?", (price, uid))
    else:
        if box < price: return await callback.answer("Недостаточно валюты Box!", show_alert=True)
        cursor.execute("UPDATE users SET box=box-? WHERE id=?", (price, uid))

    # Добавляем кастомные эмодзи к названиям домов
    if "Особняк" in h_name:
        h_name = f'<tg-emoji emoji-id="5323276453431775004">🏰</tg-emoji> {h_name}'
    elif "Императора" in h_name:
        h_name = f'<tg-emoji emoji-id="5285322720790224022">😀</tg-emoji> {h_name}'
    elif "Домик" in h_name:
        h_name = f'<tg-emoji emoji-id="5416041192905265756">🏠</tg-emoji> {h_name}'

    cursor.execute("UPDATE marriages SET house=? WHERE chat_id=? AND (user_id=? OR partner_id=?)", (h_name, chat_id, uid, uid))
    conn.commit()
    await callback.message.edit_text(f"{E_SUCCESS} Поздравляем! Ваша семья переехала в: <b>{h_name}</b>", parse_mode=ParseMode.HTML)

@dp.message(F.text.lower().in_({".хакка комплимент", "комплимент", "/compliment", ".хакка подарок", "подарок", "/gift"}))
async def cmd_marriage_actions(message: types.Message):
    chat_id, uid = message.chat.id, message.from_user.id
    if await check_offend_status(message, chat_id, uid): return

    cursor.execute("SELECT partner_id FROM marriages WHERE chat_id=? AND user_id=?", (chat_id, uid))
    m = cursor.fetchone()
    if not m: return await message.reply(f"{E_OFFENDED} Это действие доступно только для тех, кто состоит в браке!", parse_mode=ParseMode.HTML)
    
    action_type = "compliment" if "комплимент" in message.text.lower() or "compliment" in message.text.lower() else "gift"
    
    cursor.execute("SELECT template FROM marriage_actions WHERE action_type=? ORDER BY RANDOM() LIMIT 1", (action_type,))
    res = cursor.fetchone()
    if not res: 
        return await message.reply("Админы еще не добавили фразы для этого действия в базу :(")

    try:
        p_info = await bot.get_chat(m[0])
        p_name = p_info.first_name
    except: p_name = "свою половинку"

    final_text = res[0].replace("{user1}", message.from_user.first_name).replace("{user2}", p_name)
    # ИСПРАВЛЕНИЕ: отправляем реплаем
    await message.reply(f"<blockquote>{final_text}</blockquote>", parse_mode=ParseMode.HTML)


# --- 5. КАРТОЧКИ И ЕЖЕДНЕВКА ---
@dp.message(F.text.lower().in_({".хакка ежа", "ежедневка", "/daily"}))
async def cmd_daily(message: types.Message):
    uid = message.from_user.id
    c, s, last_daily, _, _, box = get_u(uid, message.from_user.username)
    now = time.time()
    last_t = float(last_daily) if last_daily else 0
    
    if now - last_t < 86400:
        return await message.reply("⏳ Награда уже получена! Приходи завтра.")

    new_s = s + 1 if (now - last_t) < 172800 else 1
    base_reward = 50
    bonus_reward = new_s * 10
    reward = base_reward + bonus_reward
    
    cursor.execute("UPDATE users SET coins=?, series=?, last_daily=? WHERE id=?", (c + reward, new_s, str(now), uid))
    conn.commit()
    
    daily_text = (
        f"{E_DAILY_MAIN} <b>Ежедневная награда</b> {E_DAILY_MAIN}\n\n"
        f"{E_DAILY_RECEIVED} <b>Получено:</b> {reward} Hacoins\n"
        f"  ┝ {E_DAILY_BASE} Базовые: {base_reward}\n"
        f"  ┕ {E_DAILY_BONUS} Бонус с Серии: {bonus_reward}\n\n"
        f"{E_DAILY_SERIES} <b>Текущая серия:</b> {new_s} дней"
    )
    
    try:
        await bot.send_message(uid, daily_text, parse_mode=ParseMode.HTML)
        if message.chat.type != "private":
            await message.reply(f"✅ <b>{message.from_user.first_name}</b>, ежедневная награда выдана! Подробности отправлены в ЛС.", parse_mode=ParseMode.HTML)
    except Exception:
        await message.reply(daily_text, parse_mode=ParseMode.HTML)

@dp.message(or_f(F.text.lower().startswith("карту"), Command("card")))
async def cmd_draw_card(message: types.Message):
    uid = message.from_user.id
    c, s, _, last_card_t, _, box = get_u(uid, message.from_user.username)
    
    now = time.time()
    if now - last_card_t < 3600:
        remains = int((3600 - (now - last_card_t)) // 60)
        return await message.reply(f"⏳ Следующая карта доступна через {remains} мин.")

    r_name = random.choices(list(RARITIES.keys()), weights=[v["chance"] for v in RARITIES.values()])[0]
    cursor.execute("SELECT id, name, photo_id, description FROM cards WHERE rarity=? ORDER BY RANDOM() LIMIT 1", (r_name,))
    card = cursor.fetchone()
    
    if not card: return await message.reply(f"В базе еще нет карт редкости {r_name}!")

    c_id, c_name, c_photo, c_desc = card
    
    min_r, max_r = RARITIES[r_name]["reward"]
    reward = random.randint(min_r, max_r)
    
    cursor.execute("UPDATE users SET coins=?, last_card_time=? WHERE id=?", (c + reward, now, uid))
    cursor.execute("INSERT INTO user_cards (user_id, card_id) VALUES (?, ?)", (uid, c_id))
    conn.commit()

    caption = (
        f"{E_CARD_STAR} <b>{message.from_user.first_name} получил(а) карту!</b> {E_CARD_STAR}\n\n"
        f"{E_CARD_STAR} <b>Название:</b> {c_name}\n"
        f"{RARITIES[r_name]['emoji']} <b>Редкость:</b> {r_name}\n"
        f"{E_REWARD_STAR} <b>Награда:</b> +{reward} Hacoins\n\n"
        f"{E_TIME_STAR} <b>Следующая карта через 1 час</b>"
    )
    
    try:
        await message.answer_photo(photo=c_photo, caption=caption, parse_mode=ParseMode.HTML)
    except Exception:
        await message.answer_animation(animation=c_photo, caption=caption, parse_mode=ParseMode.HTML)

@dp.message(Command("mycards"))
async def cmd_mycards(message: types.Message):
    uid = message.from_user.id
    
    cursor.execute("""
        SELECT cards.id, cards.name, cards.rarity, COUNT(*) 
        FROM user_cards 
        JOIN cards ON user_cards.card_id = cards.id 
        WHERE user_cards.user_id=? 
        GROUP BY cards.id
    """, (uid,))
    
    my_cards = cursor.fetchall()
    
    if not my_cards: return await message.answer("📭 Ваша коллекция пока пуста.")

    builder = InlineKeyboardBuilder()
    text = "<b>🎴 Ваша коллекция:</b>\n\n"
    
    for cid, name, rarity, count in my_cards:
        count_str = f" (x{count})" if count > 1 else ""
        text += f"{RARITIES[rarity]['emoji']} {name}{count_str}\n"
        builder.button(text=f"👁 {name}{count_str}", callback_data=f"view_{cid}")
    
    builder.adjust(2)
    await message.answer(text, reply_markup=builder.as_markup(), parse_mode=ParseMode.HTML)

@dp.callback_query(F.data.startswith("view_"))
async def view_card_detail(callback: types.CallbackQuery):
    cid = callback.data.split("_")[1]
    cursor.execute("SELECT name, rarity, photo_id, description FROM cards WHERE id=?", (cid,))
    card = cursor.fetchone()
    if card:
        name, rarity, photo_id, desc = card
        caption = f"{E_CARD_STAR} <b>Карточка: {name}</b>\n{RARITIES[rarity]['emoji']} <b>Редкость:</b> {rarity}\n━━━━━━━━━━━━━━\n<blockquote>{desc}</blockquote>"
        
        try:
            await callback.message.answer_photo(photo=photo_id, caption=caption, parse_mode=ParseMode.HTML)
        except Exception:
            await callback.message.answer_animation(animation=photo_id, caption=caption, parse_mode=ParseMode.HTML)
            
    await callback.answer()


# ====================================================================================
# --- 6. НОВАЯ АДМИН ПАНЕЛЬ И РПГ СИСТЕМА + ВЫДАЧА И КОМПЕНСАЦИИ ---
# ====================================================================================

@dp.message(F.text.lower().startswith("компенсация"), F.from_user.id.in_(ADMINS))
async def cmd_compensation(message: types.Message):
    parts = message.text.split()
    amount = 500
    
    if "всем" in message.text.lower():
        if len(parts) > 2 and parts[2].isdigit():
            amount = int(parts[2])
        cursor.execute("UPDATE users SET coins = coins + ?", (amount,))
        conn.commit()
        return await message.reply(f"✅ Массовая компенсация ({amount} {E_COINS}) успешно выдана всем пользователям в базе!")

    if len(parts) > 1 and parts[-1].isdigit():
        amount = int(parts[-1])
        
    target_id = None
    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
    elif len(parts) > 1 and parts[1].startswith('@'):
        username = parts[1][1:]
        cursor.execute("SELECT id FROM users WHERE username=?", (username,))
        res = cursor.fetchone()
        if res: target_id = res[0]
    elif len(parts) > 1 and parts[1].isdigit():
        target_id = int(parts[1])
        
    if target_id:
        cursor.execute("UPDATE users SET coins = coins + ? WHERE id = ?", (amount, target_id))
        conn.commit()
        await message.reply(f"✅ Выдана индивидуальная компенсация: {amount} {E_COINS}!")
    else:
        await message.reply("❌ Укажите кому выдать компенсацию: ответьте на сообщение, укажите ID или @username.\nПример: <code>Компенсация @username 500</code> или <code>Компенсация 500</code> (ответом на сообщение)")

@dp.message(Command("admin"), F.from_user.id.in_(ADMINS))
async def cmd_admin(message: types.Message, state: FSMContext):
    await state.clear()
    builder = InlineKeyboardBuilder()
    builder.button(text="🃏 Добавить Карточку", callback_data="adm_card_menu")
    builder.button(text="📝 Изменить Карточку", callback_data="adm_cards_edit_list")
    builder.button(text="🎭 РПГ (Обычное)", callback_data="adm_rpg_add_0")
    builder.button(text="💍 РПГ (Брак)", callback_data="adm_rpg_add_1")
    builder.button(text="💬 Добавить Комплимент", callback_data="adm_add_compliment")
    builder.button(text="🎁 Добавить Подарок", callback_data="adm_add_gift")
    builder.button(text="💰 Выдать монеты", callback_data="adm_give_coins")
    builder.button(text="📈 Уровень семьи", callback_data="adm_give_lvl")
    builder.button(text="✏️ Управление РПГ", callback_data="adm_rpg_list")
    
    builder.adjust(1, 1, 2, 2, 2, 1)
    await message.answer("👑 <b>Админ-панель:</b>", reply_markup=builder.as_markup(), parse_mode=ParseMode.HTML)

@dp.callback_query(F.data == "adm_give_coins", F.from_user.id.in_(ADMINS))
async def adm_give_coins_btn(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(AdminPanel.wait_give_coins)
    await callback.message.edit_text("Отправь ID (или @username) и сумму через пробел.\nПример: <code>123456789 500</code> или <code>@Anya 500</code>", parse_mode=ParseMode.HTML)

@dp.message(AdminPanel.wait_give_coins, F.from_user.id.in_(ADMINS))
async def adm_give_coins_save(message: types.Message, state: FSMContext):
    parts = message.text.split()
    if len(parts) == 2:
        target = parts[0]
        amount = parts[1]
        if amount.lstrip('-').isdigit():
            amount = int(amount)
            if target.startswith('@'):
                cursor.execute("SELECT id FROM users WHERE username=?", (target[1:],))
                res = cursor.fetchone()
                if not res:
                    return await message.reply("❌ Пользователь с таким юзернеймом не найден в базе.")
                target_id = res[0]
            elif target.isdigit():
                target_id = int(target)
            else:
                return await message.reply("❌ Неверный формат ID или юзернейма.")
                
            cursor.execute("UPDATE users SET coins = coins + ? WHERE id = ?", (amount, target_id))
            if cursor.rowcount > 0:
                conn.commit()
                await message.reply(f"✅ Пользователю успешно выдано {amount} {E_COINS}.")
            else:
                await message.reply("❌ Пользователь не найден в базе.")
            await state.clear()
            return
    await message.reply("❌ Неверный формат. Нужно: ID/@username сумма")

@dp.callback_query(F.data == "adm_give_lvl", F.from_user.id.in_(ADMINS))
async def adm_give_lvl_btn(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(AdminPanel.wait_give_lvl)
    await callback.message.edit_text("Отправь ID одного из супругов (или @username) и кол-во уровней.\nПример: <code>123456789 2</code>", parse_mode=ParseMode.HTML)

@dp.message(AdminPanel.wait_give_lvl, F.from_user.id.in_(ADMINS))
async def adm_give_lvl_save(message: types.Message, state: FSMContext):
    parts = message.text.split()
    if len(parts) == 2:
        target = parts[0]
        amount = parts[1]
        if amount.lstrip('-').isdigit():
            amount = int(amount)
            if target.startswith('@'):
                cursor.execute("SELECT id FROM users WHERE username=?", (target[1:],))
                res = cursor.fetchone()
                if not res: return await message.reply("❌ Пользователь не найден.")
                target_id = res[0]
            elif target.isdigit():
                target_id = int(target)
            else:
                return await message.reply("❌ Неверный формат ID/юзернейма.")

            cursor.execute("UPDATE marriages SET lvl = lvl + ? WHERE user_id = ? OR partner_id = ?", (amount, target_id, target_id))
            if cursor.rowcount > 0:
                conn.commit()
                await message.reply(f"✅ Уровень семьи (где состоит {target_id}) повышен на {amount}.")
            else:
                await message.reply("❌ Брак для этого пользователя не найден.")
            await state.clear()
            return
    await message.reply("❌ Неверный формат. Нужно: ID уровни")

@dp.callback_query(F.data == "adm_add_compliment", F.from_user.id.in_(ADMINS))
async def adm_add_compliment(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(AdminPanel.m_wait_compliment)
    await callback.message.edit_text("Отправьте текст комплимента.\nИспользуйте переменные <code>{user1}</code> (отправитель) и <code>{user2}</code> (его половинка).\n\nПример: <i>{user1} нежно шепчет {user2}, что она прекрасна!</i>", parse_mode=ParseMode.HTML)

@dp.message(AdminPanel.m_wait_compliment)
async def save_compliment(message: types.Message, state: FSMContext):
    cursor.execute("INSERT INTO marriage_actions (action_type, template) VALUES ('compliment', ?)", (message.text,))
    conn.commit()
    await message.reply("✅ Комплимент успешно добавлен в базу!")
    await state.clear()

@dp.callback_query(F.data == "adm_add_gift", F.from_user.id.in_(ADMINS))
async def adm_add_gift(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(AdminPanel.m_wait_gift)
    await callback.message.edit_text("Отправьте текст подарка.\nИспользуйте переменные <code>{user1}</code> и <code>{user2}</code>.\n\nПример: <i>{user1} дарит {user2} огромный букет роз 🌹</i>", parse_mode=ParseMode.HTML)

@dp.message(AdminPanel.m_wait_gift)
async def save_gift(message: types.Message, state: FSMContext):
    cursor.execute("INSERT INTO marriage_actions (action_type, template) VALUES ('gift', ?)", (message.text,))
    conn.commit()
    await message.reply("✅ Подарок успешно добавлен в базу!")
    await state.clear()

async def show_card_builder(message_or_callback, state: FSMContext):
    data = await state.get_data()
    text = (
        f"🛠 <b>Конструктор карточки:</b>\n\n"
        f"🖼 <b>Медиа:</b> {'✅ Загружено' if data.get('cb_photo') else '❌ Нет'}\n"
        f"📝 <b>Название:</b> {data.get('cb_name', '❌ Нет')}\n"
        f"📖 <b>Описание:</b> {data.get('cb_desc', '❌ Нет')}\n"
        f"💎 <b>Редкость:</b> {data.get('cb_rarity', '❌ Нет')}\n"
    )
    builder = InlineKeyboardBuilder()
    builder.button(text="🖼 Медиа", callback_data="cbuild_photo")
    builder.button(text="📝 Название", callback_data="cbuild_name")
    builder.button(text="📖 Описание", callback_data="cbuild_desc")
    builder.button(text="💎 Редкость", callback_data="cbuild_rarity")
    
    if data.get('cb_photo') and data.get('cb_name') and data.get('cb_desc') and data.get('cb_rarity'):
        if data.get('cb_card_id'):
            builder.button(text="💾 СОХРАНИТЬ ИЗМЕНЕНИЯ", callback_data="cbuild_update")
        else:
            builder.button(text="✅ ДОБАВИТЬ В БАЗУ", callback_data="cbuild_save")
    
    builder.button(text="🔙 Назад", callback_data="adm_back")
    builder.adjust(2, 2, 1, 1)

    if isinstance(message_or_callback, types.CallbackQuery):
        await message_or_callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode=ParseMode.HTML)
    else:
        await message_or_callback.answer(text, reply_markup=builder.as_markup(), parse_mode=ParseMode.HTML)

@dp.callback_query(F.data == "adm_card_menu", F.from_user.id.in_(ADMINS))
async def adm_card_menu(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await show_card_builder(callback, state)

@dp.callback_query(F.data == "adm_cards_edit_list", F.from_user.id.in_(ADMINS))
async def adm_cards_edit_list(callback: types.CallbackQuery, state: FSMContext):
    cursor.execute("SELECT id, name FROM cards ORDER BY id DESC LIMIT 90")
    cards = cursor.fetchall()
    
    if not cards:
        return await callback.answer("База карточек пуста!", show_alert=True)
        
    builder = InlineKeyboardBuilder()
    for cid, name in cards:
        builder.button(text=name, callback_data=f"cedit_{cid}")
        
    builder.button(text="🔙 Назад", callback_data="adm_back")
    builder.adjust(2)
    
    await callback.message.edit_text("Выбери карточку для изменения:", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("cedit_"), F.from_user.id.in_(ADMINS))
async def adm_card_edit_start(callback: types.CallbackQuery, state: FSMContext):
    cid = callback.data.split("_")[1]
    cursor.execute("SELECT name, rarity, photo_id, description FROM cards WHERE id=?", (cid,))
    card = cursor.fetchone()
    
    if not card: 
        return await callback.answer("Карта не найдена!", show_alert=True)
    
    await state.update_data(
        cb_card_id=cid,
        cb_name=card[0],
        cb_rarity=card[1],
        cb_photo=card[2],
        cb_desc=card[3]
    )
    await show_card_builder(callback, state)

@dp.callback_query(F.data.startswith("cbuild_"), F.from_user.id.in_(ADMINS))
async def cbuild_actions(callback: types.CallbackQuery, state: FSMContext):
    action = callback.data.split("_")[1]
    
    if action == "photo":
        await state.set_state(AdminPanel.cb_wait_photo)
        await callback.message.edit_text("Отправь фото или GIF для карточки:")
    elif action == "name":
        await state.set_state(AdminPanel.cb_wait_name)
        await callback.message.edit_text("Отправь название карточки:")
    elif action == "desc":
        await state.set_state(AdminPanel.cb_wait_desc)
        await callback.message.edit_text("Отправь описание карточки:")
    elif action == "rarity":
        builder = InlineKeyboardBuilder()
        for r in RARITIES.keys():
            # ИСПРАВЛЕНИЕ: Используем base emoji, чтобы HTML не ломал кнопки
            builder.button(text=f"{RARITIES[r]['base']} {r}", callback_data=f"csetrarity_{r}")
        builder.adjust(2)
        await callback.message.edit_text("Выбери редкость (строго из списка):", reply_markup=builder.as_markup())
    elif action == "save":
        data = await state.get_data()
        cursor.execute("INSERT INTO cards (name, rarity, photo_id, description) VALUES (?, ?, ?, ?)",
                       (data['cb_name'], data['cb_rarity'], data['cb_photo'], data['cb_desc']))
        conn.commit()
        await callback.message.edit_text(f"✅ Карточка <b>{data['cb_name']}</b> успешно сохранена в базу!", parse_mode=ParseMode.HTML)
        await state.clear()
    elif action == "update":
        data = await state.get_data()
        cursor.execute("UPDATE cards SET name=?, rarity=?, photo_id=?, description=? WHERE id=?",
                       (data['cb_name'], data['cb_rarity'], data['cb_photo'], data['cb_desc'], data['cb_card_id']))
        conn.commit()
        await callback.message.edit_text(f"✅ Изменения карточки <b>{data['cb_name']}</b> успешно сохранены!", parse_mode=ParseMode.HTML)
        await state.clear()

@dp.callback_query(F.data.startswith("csetrarity_"), F.from_user.id.in_(ADMINS))
async def cset_rarity(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(cb_rarity=callback.data.split("_")[1])
    await show_card_builder(callback, state)

@dp.message(AdminPanel.cb_wait_photo, F.photo | F.animation)
async def cbuild_get_photo(message: types.Message, state: FSMContext):
    fid = message.photo[-1].file_id if message.photo else message.animation.file_id
    await state.update_data(cb_photo=fid)
    await show_card_builder(message, state)

@dp.message(AdminPanel.cb_wait_name)
async def cbuild_get_name(message: types.Message, state: FSMContext):
    await state.update_data(cb_name=message.text)
    await show_card_builder(message, state)

@dp.message(AdminPanel.cb_wait_desc)
async def cbuild_get_desc(message: types.Message, state: FSMContext):
    await state.update_data(cb_desc=message.text)
    await show_card_builder(message, state)

@dp.callback_query(F.data == "adm_back")
async def adm_back(callback: types.CallbackQuery, state: FSMContext):
    await cmd_admin(callback.message, state)
    await callback.message.delete()

@dp.callback_query(F.data.startswith("adm_rpg_add_"), F.from_user.id.in_(ADMINS))
async def adm_rpg_start(callback: types.CallbackQuery, state: FSMContext):
    is_marriage = int(callback.data.split("_")[3])
    await state.update_data(is_marriage=is_marriage)
    await state.set_state(AdminPanel.rpg_wait_trigger)
    await callback.message.edit_text("Отправь слово-команду (например: засосать или /засосать):")

@dp.message(AdminPanel.rpg_wait_trigger)
async def adm_rpg_get_trigger(message: types.Message, state: FSMContext):
    trigger = message.text.lower().strip()
    await state.update_data(rpg_trigger=trigger)
    
    data = await state.get_data()
    example = "&lt;blockquote&gt;{fam1} поцеловал свою половинку {fam2} &lt;tg-emoji emoji-id='5364050751226127978'&gt;🤪&lt;/tg-emoji&gt;&lt;/blockquote&gt;" if data.get('is_marriage') else "&lt;blockquote&gt;{user1} страстно засосал(а) {user2} &lt;tg-emoji emoji-id='...'&gt;💋&lt;/tg-emoji&gt;&lt;/blockquote&gt;"
    
    await state.set_state(AdminPanel.rpg_wait_template)
    await message.answer(f"Отправь HTML шаблон для ответа.\nИспользуй переменные.\nПример:\n<code>{example}</code>", parse_mode=ParseMode.HTML)

@dp.message(AdminPanel.rpg_wait_template)
async def adm_rpg_get_template(message: types.Message, state: FSMContext):
    data = await state.get_data()
    trigger = data['rpg_trigger']
    is_marriage = data['is_marriage']
    
    cursor.execute("REPLACE INTO rp_commands (command, template, is_marriage) VALUES (?, ?, ?)", (trigger, message.text, is_marriage))
    conn.commit()
    
    await message.answer(f"✅ Текст команды <b>{trigger}</b> обновлен!", parse_mode=ParseMode.HTML)
    await state.clear()

@dp.callback_query(F.data == "adm_rpg_list", F.from_user.id.in_(ADMINS))
async def adm_rpg_list(callback: types.CallbackQuery):
    cursor.execute("SELECT command, is_marriage FROM rp_commands")
    commands = cursor.fetchall()
    
    if not commands:
        return await callback.answer("База РПГ команд пуста!", show_alert=True)
        
    builder = InlineKeyboardBuilder()
    for cmd, is_m in commands:
        prefix = "💍" if is_m else "🎭"
        builder.button(text=f"{prefix} {cmd}", callback_data=f"rpgact_{cmd}")
    builder.button(text="🔙 Назад", callback_data="adm_back")
    builder.adjust(2)
    
    await callback.message.edit_text("Выбери команду для настройки:", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("rpgact_"), F.from_user.id.in_(ADMINS))
async def adm_rpg_action(callback: types.CallbackQuery, state: FSMContext):
    trigger = callback.data.replace("rpgact_", "")
    await state.update_data(edit_rpg_trigger=trigger)
    
    builder = InlineKeyboardBuilder()
    builder.button(text="🗑 Удалить", callback_data="rpgdel_confirm")
    builder.button(text="✏️ Изменить текст", callback_data="rpgedit_start")
    builder.button(text="🔙 Назад", callback_data="adm_rpg_list")
    builder.adjust(2, 1)
    
    await callback.message.edit_text(f"Команда: <b>{trigger}</b>\nЧто сделать?", reply_markup=builder.as_markup(), parse_mode=ParseMode.HTML)

@dp.callback_query(F.data == "rpgdel_confirm", F.from_user.id.in_(ADMINS))
async def adm_rpg_delete(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    trigger = data.get('edit_rpg_trigger')
    cursor.execute("DELETE FROM rp_commands WHERE command=?", (trigger,))
    conn.commit()
    await callback.answer(f"Команда {trigger} удалена!", show_alert=True)
    await adm_rpg_list(callback)

@dp.callback_query(F.data == "rpgedit_start", F.from_user.id.in_(ADMINS))
async def adm_rpg_edit(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(AdminPanel.rpg_wait_edit_template)
    await callback.message.edit_text("Отправь новый HTML шаблон для этой команды:")

@dp.message(AdminPanel.rpg_wait_edit_template)
async def adm_rpg_save_edit(message: types.Message, state: FSMContext):
    data = await state.get_data()
    trigger = data.get('edit_rpg_trigger')
    
    cursor.execute("UPDATE rp_commands SET template=? WHERE command=?", (message.text, trigger))
    conn.commit()
    
    await message.answer(f"✅ Шаблон для <b>{trigger}</b> успешно изменен!", parse_mode=ParseMode.HTML)
    await state.clear()

# ====================================================================================
# --- 7. КРЕСТИКИ-НОЛИКИ ---
# ====================================================================================

@dp.message(Command("ttt"))
async def cmd_ttt(message: types.Message):
    if not message.reply_to_message:
        return await message.reply("Для игры в Крестики-Нолики ответьте на сообщение друга этой командой!")
        
    p_x = message.from_user.id
    p_o = message.reply_to_message.from_user.id
    
    if p_x == p_o:
        return await message.reply("Нельзя играть с самим собой!")

    game_id = str(uuid.uuid4())[:8]
    active_ttt_games[game_id] = {
        "x": p_x,
        "o": p_o,
        "board": [" "] * 9,
        "turn": "x",
        "start_time": time.time()
    }

    builder = InlineKeyboardBuilder()
    for i in range(9):
        builder.button(text=TTT_E_EMPTY, callback_data=f"ttt_{game_id}_{i}")
    builder.adjust(3, 3, 3)

    text = f"🎮 <b>Крестики-Нолики</b>\n\n✖️ {message.from_user.first_name}\n⭕️ {message.reply_to_message.from_user.first_name}\n\nСейчас ходит: <b>Крестик</b>"
    await message.reply(text, reply_markup=builder.as_markup(), parse_mode=ParseMode.HTML)

@dp.callback_query(F.data.startswith("ttt_"))
async def ttt_callback(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    game_id = parts[1]
    cell_idx = int(parts[2])

    if game_id not in active_ttt_games:
        return await callback.answer("Эта игра не найдена или уже завершена!", show_alert=True)

    game = active_ttt_games[game_id]

    # Проверка таймаута (10 минут)
    if time.time() - game["start_time"] > 600:
        del active_ttt_games[game_id]
        return await callback.message.edit_text("⏳ Игра отменена по таймауту (прошло более 10 минут).")

    uid = callback.from_user.id
    current_turn = game["turn"]
    
    if (current_turn == "x" and uid != game["x"]) or (current_turn == "o" and uid != game["o"]):
        return await callback.answer("Сейчас не твой ход или ты не в этой игре!", show_alert=True)

    if game["board"][cell_idx] != " ":
        return await callback.answer("Эта клетка уже занята!", show_alert=True)

    game["board"][cell_idx] = current_turn

    win_combos = [(0,1,2), (3,4,5), (6,7,8), (0,3,6), (1,4,7), (2,5,8), (0,4,8), (2,4,6)]
    winner = None
    for a, b, c in win_combos:
        if game["board"][a] == game["board"][b] == game["board"][c] != " ":
            winner = game["board"][a]
            break

    is_draw = " " not in game["board"] and not winner

    if winner or is_draw:
        builder = InlineKeyboardBuilder()
        for cell in game["board"]:
            text = TTT_E_EMPTY
            if cell == "x": text = TTT_E_X
            elif cell == "o": text = TTT_E_O
            builder.button(text=text, callback_data="ignore")
        builder.adjust(3, 3, 3)

        if winner:
            win_word = "Крестик" if winner == "x" else "Нолик"
            res_text = f"🎉 <b>ПОБЕДА!</b> Выиграл <b>{win_word}</b>!"
        else:
            res_text = "🤝 <b>НИЧЬЯ!</b>"
            
        await callback.message.edit_text(res_text, reply_markup=builder.as_markup(), parse_mode=ParseMode.HTML)
        del active_ttt_games[game_id]
        return

    game["turn"] = "o" if current_turn == "x" else "x"
    builder = InlineKeyboardBuilder()
    for i, cell in enumerate(game["board"]):
        text = TTT_E_EMPTY
        if cell == "x": text = TTT_E_X
        elif cell == "o": text = TTT_E_O
        builder.button(text=text, callback_data=f"ttt_{game_id}_{i}")
    builder.adjust(3, 3, 3)

    next_turn_word = "Крестик" if game["turn"] == "x" else "Нолик"
    await callback.message.edit_text(f"🎮 <b>Крестики-Нолики</b>\n\nСейчас ходит: <b>{next_turn_word}</b>", reply_markup=builder.as_markup(), parse_mode=ParseMode.HTML)

@dp.message(F.text.lower().in_({"/stopttt", "стоп игра"}), F.from_user.id.in_(ADMINS))
async def cmd_stop_ttt(message: types.Message):
    if not active_ttt_games:
        return await message.reply("В данный момент нет активных игр в Крестики-Нолики.")

    builder = InlineKeyboardBuilder()
    for gid, game in active_ttt_games.items():
        dur = int((time.time() - game["start_time"]) // 60)
        builder.button(text=f"Игра {gid} ({dur} мин)", callback_data=f"stopttt_{gid}")
    builder.adjust(1)
    await message.reply("Выберите игру для принудительного завершения:", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("stopttt_"), F.from_user.id.in_(ADMINS))
async def cb_stop_ttt(callback: types.CallbackQuery):
    gid = callback.data.split("_")[1]
    if gid in active_ttt_games:
        del active_ttt_games[gid]
        await callback.message.edit_text(f"✅ Игра {gid} была принудительно отменена.")
    else:
        await callback.answer("Эта игра уже завершена.", show_alert=True)


# ====================================================================================
# --- 8. ГЛОБАЛЬНЫЙ ОБРАБОТЧИК РПГ КОМАНД ---
# ====================================================================================
@dp.message(F.text)
async def global_rp_handler(message: types.Message):
    text = message.text.lower().strip()
    
    cursor.execute("SELECT template, is_marriage FROM rp_commands WHERE command=? OR command=?", (text, f"/{text}"))
    res = cursor.fetchone()
    
    if res:
        template, is_marriage = res
        
        if not message.reply_to_message:
            return await message.reply("Эту команду нужно использовать ответом на сообщение пользователя!")
            
        user1 = message.from_user.first_name
        user2 = message.reply_to_message.from_user.first_name
        
        if is_marriage == 1:
            uid = message.from_user.id
            tid = message.reply_to_message.from_user.id
            chat_id = message.chat.id
            
            cursor.execute("SELECT * FROM marriages WHERE chat_id=? AND ((user_id=? AND partner_id=?) OR (user_id=? AND partner_id=?))", 
                           (chat_id, uid, tid, tid, uid))
            if not cursor.fetchone():
                return await message.reply(f"{E_OFFENDED} <b>Ошибка:</b> Эта команда доступна только если вы состоите в браке с этим пользователем!", parse_mode=ParseMode.HTML)
                
            final_text = template.replace("{fam1}", user1).replace("{fam2}", user2).replace("|", "")
        else:
            final_text = template.replace("{user1}", user1).replace("{user2}", user2).replace("|", "")
            
        await message.reply(final_text, parse_mode=ParseMode.HTML)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
