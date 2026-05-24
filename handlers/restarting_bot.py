import database.requests as db
from aiogram import Bot
import asyncio
from datetime import datetime
import database.requests as db

# Функция для отправки сообщений администраторам или создателю
async def notify_admins_or_creator(bot: Bot, group_id: int, text: str) -> None:
    
    admins = await bot.get_chat_administrators(group_id)
    
    # Ищем создателя
    creator = None
    for admin in admins:
        if admin.status == 'creator':
            creator = admin.user.id
            break
    
    if creator:
        try:
            await bot.send_message(chat_id=creator, text=text, parse_mode="Markdown")
            print(f"Уведомление отправлено создателю {creator}")
        except Exception as e:
            print(f"Не удалось отправить создателю: {e}")
    else:
        # Если нету создателя, то отправляем всем администраторам
        for admin in admins:
            if admin.status == 'administrator':
                try:
                    await bot.send_message(chat_id=admin.user.id, text=text, parse_mode="Markdown")
                    print(f"Уведомление отправлено администратору {admin.user.id}")
                except Exception as e:
                    print(f"Не удалось отправить администратору: {e}")


# Получаем все группы из последних 100 сообщений
async def get_all_bot_groups(bot: Bot):
    updates = await bot.get_updates()
    groups = {}
    
    for update in updates:
        if update.message and update.message.chat.type in ['group', 'supergroup']:
            chat = update.message.chat
            groups[chat.id] = chat.title
    
    return groups


async def restore_bot_status(bot: Bot):
    # Новые группы (которые есть в get_updates, но нет в БД)
    bot_groups = await get_all_bot_groups(bot)
    for group_id, group_name in bot_groups.items():
        existing_group = await db.get_group_by_id(group_id)
        
        if not existing_group:
            try:
                bot_member = await bot.get_chat_member(group_id, bot.id)
                
                if bot_member.status in ['administrator', 'creator']:
                    await db.add_group(group_id, group_name)
                    await db.activate_group(group_id)
                    print(f"Новая группа добавлена и активирована: {group_name}")

                    
                elif bot_member.status == 'member':
                    await db.add_group(group_id, group_name)
                    print(f"Новая группа добавлена (бот не админ): {group_name}")
                    
                else:
                    # Статус 'left' или 'kicked' - бота нет в группе
                    print(f"Бот не найден в группе {group_name}, пропускаем.")
                    
            except Exception as e:
                print(f"Ошибка при проверке новой группы {group_name}: {e}")



# Периодическая функция для проверки на удаление бота
async def periodic_status_check(bot: Bot, interval_seconds: int = 10):
    while True:
        try:
            await asyncio.sleep(interval_seconds)
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Проверка удаления бота...")
            
            # Получаем все группы из БД
            db_groups = await db.get_all_groups()
            
            for db_group in db_groups:
                try:
                    bot_member = await bot.get_chat_member(db_group.group_id, bot.id)
                    
                    # Если бот не в группе (left, kicked) - удаляем
                    if bot_member.status in ['left', 'kicked']:
                        print(f"Бот удалён из {db_group.group_name}, удаляем из БД")
                        await db.remove_group(db_group.group_id)
                        
                except Exception as e:
                    # Ошибка при проверке - бота нет в группе
                    print(f"Группа {db_group.group_name} удалена (ошибка: {e})")
                    await db.remove_group(db_group.group_id)
                    
        except Exception as e:
            print(f"Ошибка в periodic_status_check: {e}")
            await asyncio.sleep(5)