import random
from aiogram import Router, types, F, Bot
from aiogram.filters import Command, CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import ReplyKeyboardRemove
from config import PORCUPINE_GIFS, ADMIN_IDS
from database.models import (
    get_or_create_user, get_active_car, claim_daily, get_user_crew,
    get_user_cases, get_user_custom_bonuses
)
from game.cars import get_car
from game.media import get_amg_gif
from game.utils import escape_md

router = Router()

def get_main_screen_markup(cases_cnt: int = 1, is_admin_user: bool = False) -> types.InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    # 1. Основные режимы гонок и гараж
    builder.button(text="🏎 МОЙ ГАРАЖ И ТЮНИНГ", callback_data="menu_garage")
    builder.button(text="⚔️ БЕСПЛАТНАЯ ДУЭЛЬ 402М", callback_data="menu_race_info")
    
    # 2. Командные активности
    builder.button(text="👹 РЕЙД НА БОССА", callback_data="menu_boss_action")
    builder.button(text="🚔 КОРТЕЖ AMG", callback_data="menu_convoy_action")
    
    # 3. Турниры и стиль
    builder.button(text="🏆 ГРАН-ПРИ ТУРНИР", callback_data="menu_gp_action")
    builder.button(text="💨 ДРИФТ-БИТВА", callback_data="menu_drift_action")
    
    # 4. Лут, рулетка и награды
    builder.button(text="🎰 РУЛЕТКА ФОРТУНЫ", callback_data="menu_wheel_action")
    builder.button(text=f"📦 КЕЙС ({cases_cnt} шт.)", callback_data="open_cases_menu")
    builder.button(text="🎁 ЕЖЕДНЕВНЫЙ БОНУС", callback_data="menu_daily")
    builder.button(text="🚨 ОБЛАВА ДПС / РОЗЫСК", callback_data="menu_police_action")
    
    # 5. Сообщество и статистика
    builder.button(text="🏁 АВТОКЛУБЫ", callback_data="menu_crew_action")
    builder.button(text="📊 ТОП ЛИДЕРОВ", callback_data="menu_top_action")
    
    # 6. Профиль и управление
    builder.button(text="📋 ПРОФИЛЬ ПИЛОТА", callback_data="menu_profile_action")
    if is_admin_user:
        builder.button(text="👑 АДМИН-ПАНЕЛЬ", callback_data="menu_admin_action")
    
    # 7. Фирменная кнопка
    builder.button(text="🦔 БАХНУТЬ СОЛИ (amglive.to)", callback_data="action_salt_porcupine")
    
    if is_admin_user:
        builder.adjust(1, 1, 2, 2, 2, 2, 2, 2, 1)
    else:
        builder.adjust(1, 1, 2, 2, 2, 2, 2, 1, 1)
    return builder.as_markup()

async def render_main_screen_text(user_id: int, full_name: str, username: str) -> tuple[str, types.InlineKeyboardMarkup]:
    user = await get_or_create_user(
        user_id=user_id,
        username=username,
        full_name=full_name
    )
    active_car_data = await get_active_car(user_id)
    car = get_car(active_car_data["car_key"]) if active_car_data else None
    car_name = car["name"] if car else "Mercedes-AMG A 45 S"
    cases_cnt = await get_user_cases(user_id)
    power_b, grip_b = await get_user_custom_bonuses(user_id)
    crew = await get_user_crew(user_id)
    crew_tag = f"[{escape_md(crew['tag'])}] " if crew else ""
    pilot_name = escape_md(full_name)
    is_admin_user = (user_id in ADMIN_IDS)

    text = (
        f"🏁 *ГЛАВНОЕ МЕНЮ: MERCEDES-AMG CLUB* 🏁\n\n"
        f"👤 Пилот: *{crew_tag}{pilot_name}*\n"
        f"💰 Баланс: *{user['coins']:,} AMG Coins* | ⛽ Топливо: *{user['fuel']}/100*\n"
        f"🏎 Текущий болид: *{car_name}*\n"
        f"⚡ Кастомные детали: *+{power_b} л.с.* | *+{grip_b} зацепа*\n"
        f"📦 Кейсов Аффальтербаха: *{cases_cnt} шт.*\n\n"
        f"🎮 *Все режимы бесплатны для всех участников! Выберите действие:*"
    ).replace(",", " ")

    return text, get_main_screen_markup(cases_cnt, is_admin_user=is_admin_user)

@router.message(CommandStart())
@router.message(Command("menu"))
async def cmd_start(message: types.Message):
    # Гарантированно убираем нижнюю клавиатуру в клиенте Telegram (в личке и группах)
    try:
        await message.answer("🏁 *Mercedes-AMG Club*", reply_markup=ReplyKeyboardRemove(remove_keyboard=True), parse_mode="Markdown")
    except Exception:
        pass

    text, markup = await render_main_screen_text(
        user_id=message.from_user.id,
        full_name=message.from_user.full_name,
        username=message.from_user.username
    )
    await message.answer(text, reply_markup=markup, parse_mode="Markdown")

@router.callback_query(F.data == "menu_main")
async def cb_menu_main(callback: types.CallbackQuery):
    text, markup = await render_main_screen_text(
        user_id=callback.from_user.id,
        full_name=callback.from_user.full_name,
        username=callback.from_user.username
    )
    try:
        await callback.message.edit_text(text, reply_markup=markup, parse_mode="Markdown")
    except Exception:
        await callback.message.answer(text, reply_markup=markup, parse_mode="Markdown")
    await callback.answer()

# --- Инлайн-кнопки главного экрана ---
@router.callback_query(F.data == "menu_race_info")
async def cb_race_info(callback: types.CallbackQuery):
    from handlers.race_duel import cmd_race
    await cmd_race(callback.message, user=callback.from_user)
    await callback.answer()

@router.callback_query(F.data == "menu_boss_action")
async def cb_boss_action(callback: types.CallbackQuery):
    from handlers.boss import cmd_boss
    await cmd_boss(callback.message)
    await callback.answer()

@router.callback_query(F.data == "menu_convoy_action")
async def cb_convoy_action(callback: types.CallbackQuery):
    from handlers.convoy import cmd_convoy
    await cmd_convoy(callback.message, user=callback.from_user)
    await callback.answer()

@router.callback_query(F.data == "menu_gp_action")
async def cb_gp_action(callback: types.CallbackQuery):
    from handlers.grandprix import cmd_grandprix
    await cmd_grandprix(callback.message, user=callback.from_user)
    await callback.answer()

@router.callback_query(F.data == "menu_drift_action")
async def cb_drift_action(callback: types.CallbackQuery):
    from handlers.drift import cmd_drift
    await cmd_drift(callback.message, user=callback.from_user)
    await callback.answer()

@router.callback_query(F.data == "menu_crew_action")
async def cb_crew_action(callback: types.CallbackQuery):
    from handlers.crews import cmd_crew
    await cmd_crew(callback.message, user=callback.from_user)
    await callback.answer()

@router.callback_query(F.data == "menu_top_action")
async def cb_top_action(callback: types.CallbackQuery):
    from handlers.stats import cmd_top
    await cmd_top(callback.message)
    await callback.answer()

@router.callback_query(F.data == "menu_profile_action")
async def cb_profile_action(callback: types.CallbackQuery):
    from handlers.stats import cmd_profile
    await cmd_profile(callback.message, user=callback.from_user)
    await callback.answer()

@router.callback_query(F.data == "menu_admin_action")
async def cb_admin_action(callback: types.CallbackQuery):
    from handlers.admin import is_admin, cmd_admin
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ разрешен только администраторам.", show_alert=True)
        return
    await cmd_admin(callback.message, user=callback.from_user)
    await callback.answer()

@router.callback_query(F.data == "menu_wheel_action")
async def cb_wheel_action(callback: types.CallbackQuery):
    from handlers.wheel import cmd_wheel
    await cmd_wheel(callback.message, user=callback.from_user)
    await callback.answer()

@router.callback_query(F.data == "menu_police_action")
async def cb_police_action(callback: types.CallbackQuery):
    from handlers.police import cmd_police
    await cmd_police(callback.message, user=callback.from_user)
    await callback.answer()

async def send_salt_porcupine(target: types.Message):
    gif_url = random.choice(PORCUPINE_GIFS)
    builder = InlineKeyboardBuilder()
    builder.button(text="🌐 Перейти на amglive.to", url="https://amglive.to")
    builder.button(text="🔙 Главное меню", callback_data="menu_main")
    builder.adjust(1)

    try:
        await target.answer_animation(
            animation=gif_url,
            caption="🦔 *Дикобраз заряжен на максимум!*\n\nПереходи на сайт: https://amglive.to",
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )
    except Exception:
        await target.answer(
            "🦔 *Дикобраз заряжен!*\n\nСайт: https://amglive.to",
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )

@router.callback_query(F.data == "action_salt_porcupine")
async def cb_salt_porcupine(callback: types.CallbackQuery):
    await send_salt_porcupine(callback.message)
    await callback.answer("🦔 Заряд активирован!")

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    text = (
        "📖 *СПРАВОЧНИК MERCEDES-AMG CLUB*\n\n"
        "🏎 *Гараж и тюнинг:*\n"
        "• `/garage` — Открыть гараж, прокачать Stage 1/2/3 и кастомные детали\n"
        "• `/case` — Открыть Кейсы Аффальтербаха с редким дропом деталей\n\n"
        "⚔️ *Бесплатные заезды для всех в чате:*\n"
        "• `/race` — Мгновенный бесплатный заезд на 402м с призом победителю\n"
        "• `/convoy` — Сбор кортежа AMG на ночной автобан за монетами и кейсами\n"
        "• `/grandprix` — Турнир на 4 гонщика с Золотым Кубком\n"
        "• `/drift` — Дрифт-битва на угол заноса и стиль\n\n"
        "👹 *Рейды на Боссов:*\n"
        "• `/boss` — Совместный бой с боссом в чате\n\n"
        "🏁 *Автоклубы:*\n"
        "• `/crew` — Меню клуба, общак, прокачка перков\n"
        "• `/crew_create [Имя]` — Бесплатно создать свой автоклуб\n"
        "• `/crew_join [Имя]` — Вступить в автоклуб\n"
        "• `/crews_top` — Рейтинг клубов\n\n"
        "💰 *Профиль, рулетка и полиция:*\n"
        "• `/spin` — Колесо Фортуны Аффальтербаха (бесплатный спин раз в сутки!)\n"
        "• `/police` — Сводка розыска ДПС и план «Перехват»\n"
        "• `/daily` — Ежедневный бонус монет и бензина\n"
        "• `/profile` — Личный профиль, кубки и инвентарь\n"
        "• `/top` — Топ гонщиков чата\n"
        "• `/admin` — Панель администратора"
    )
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Главное меню", callback_data="menu_main")
    await message.answer(text, reply_markup=builder.as_markup(), parse_mode="Markdown")
