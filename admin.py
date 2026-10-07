from aiogram import Router, types, F, Bot
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import ADMIN_IDS
from database.models import (
    get_admin_stats, admin_give_coins, admin_refill_all_fuel,
    get_all_user_ids, create_chat_boss
)
from game.bosses import BOSSES_DATA
import random

from typing import Optional

router = Router()

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

@router.message(Command("admin"))
async def cmd_admin(message: types.Message, user: Optional[types.User] = None):
    caller = user or message.from_user
    if not is_admin(caller.id):
        await message.reply("⛔ У вас нет прав администратора.")
        return

    stats = await get_admin_stats()
    text = (
        f"👑 *ПАНЕЛЬ АДМИНИСТРАТОРА AMG CLUB*\n\n"
        f"📊 *Статистика игры:*\n"
        f"• 👥 Всего игроков: *{stats['total_users']:,}*\n"
        f"• 🏎 Создано автоклубов: *{stats['total_crews']}*\n"
        f"• 💰 Монет в экономике: *{stats['total_coins']:,}*\n"
        f"• 🏁 Всего заездов: *{stats['total_duels']}*\n\n"
        f"⚙️ *Быстрые команды администратора:*\n"
        f"• `/give_coins [ID] [сумма]` — выдать монеты игроку\n"
        f"• `/give_case [ID] [кол-во]` — выдать кейсы игроку\n"
        f"• `/broadcast [текст]` — отправить объявление всем игрокам бота"
    ).replace(",", " ")

    builder = InlineKeyboardBuilder()
    builder.button(text="⛽ Заправить всех игроков (100л)", callback_data="admin_refill_fuel")
    builder.button(text="👹 Призвать босса в чат", callback_data="admin_spawn_boss")
    builder.button(text="🔙 Главное меню", callback_data="menu_main")
    builder.adjust(1)

    await message.answer(text, reply_markup=builder.as_markup(), parse_mode="Markdown")

@router.callback_query(F.data == "admin_refill_fuel")
async def cb_admin_refill_fuel(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет прав.", show_alert=True)
        return

    count = await admin_refill_all_fuel()
    await callback.answer(f"Бак заправлен на 100 л для {count} игроков!", show_alert=True)

@router.callback_query(F.data == "admin_spawn_boss")
async def cb_admin_spawn_boss(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет прав.", show_alert=True)
        return

    boss_key = random.choice(list(BOSSES_DATA.keys()))
    b_data = BOSSES_DATA[boss_key]
    from handlers.boss import build_boss_message
    text, markup = build_boss_message(b_data, b_data["max_hp"], b_data["max_hp"])
    sent = await callback.message.answer(text, reply_markup=markup, parse_mode="Markdown")
    await create_chat_boss(callback.message.chat.id, boss_key, b_data["max_hp"], sent.message_id)
    await callback.answer(f"Босс {b_data['name']} успешно призван!")

@router.message(Command("give_coins"))
async def cmd_give_coins(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.reply("⛔ У вас нет прав администратора.")
        return

    args = message.text.split()[1:]
    if len(args) < 2 or not args[0].isdigit() or not args[1].isdigit():
        await message.reply("Использование: `/give_coins [user_id] [сумма]`\nПример: `/give_coins 12345678 10000`", parse_mode="Markdown")
        return

    target_id = int(args[0])
    amount = int(args[1])
    success = await admin_give_coins(target_id, amount)
    if success:
        await message.reply(f"✅ Успешно начислено 💰 {amount:,} монет игроку с ID {target_id}!".replace(",", " "))
    else:
        await message.reply(f"❌ Игрок с ID {target_id} не найден в базе данных.")

@router.message(Command("broadcast"))
async def cmd_broadcast(message: types.Message, bot: Bot):
    if not is_admin(message.from_user.id):
        await message.reply("⛔ У вас нет прав администратора.")
        return

    text = message.text.split(maxsplit=1)[1:]
    if not text:
        await message.reply("Использование: `/broadcast [текст сообщения]`")
        return

    broadcast_msg = f"📢 *ОБЪЯВЛЕНИЕ АДМИНИСТРАЦИИ AMG:*\n\n{text[0]}"
    user_ids = await get_all_user_ids()
    sent_count = 0

    for uid in user_ids:
        try:
            await bot.send_message(uid, broadcast_msg, parse_mode="Markdown")
            sent_count += 1
        except Exception:
            pass

    await message.reply(f"📢 Рассылка отправлена {sent_count}/{len(user_ids)} игрокам.")

@router.message(Command("give_case"))
async def cmd_give_case(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.reply("⛔ У вас нет прав администратора.")
        return

    args = message.text.split()[1:]
    if len(args) < 2 or not args[0].isdigit() or not args[1].isdigit():
        await message.reply("Использование: `/give_case [user_id] [кол-во]`\nПример: `/give_case 12345678 3`", parse_mode="Markdown")
        return

    target_id = int(args[0])
    count = int(args[1])
    from database.models import add_cases
    await add_cases(target_id, count)
    await message.reply(f"✅ Успешно начислено 📦 {count} кейсов игроку {target_id}!")


