from aiogram import Router, Bot, F
import database.requests as db
from aiogram.types import ChatMemberUpdated

router = Router()
    

# декоратор, который следит за изменениями событий этого бота, ChatMemberUpdatedFilter - фильтр, который отбирает нужные нам изменения статуса бота
@router.my_chat_member(F.old_chat_member.status == 'left', F.new_chat_member.status == 'member')
async def bot_added_to_group(event: ChatMemberUpdated) -> None:
    chat = event.chat
    chat_id = chat.id
    chat_title = chat.title
    bot = event.bot
    added_by = event.from_user  # кто добавил бота
    
    # добавляем группу в базу данных
    await db.add_group(chat_id, chat_title)
    
    # Уведомляем того, кто добавил бота
    try:
        await bot.send_message(
            chat_id=added_by.id,
            text= f"*Приветствую вас!*\n\nЯ Telegram бот, который будет следить за токсичностью в группе '*{chat_title}*'.\nСделайте меня администратором, и я начну свою работу:)",
            parse_mode="Markdown"
        )
        print(f"Сообщение было отправлено пользователю {added_by.id}, который добавил бота!")
    except Exception as e:
        print(f"Сообщение не было отправлено пользователю {added_by.id}, который добавил бота! Ошибка: {e}")


# Бота сделали администратором
@router.my_chat_member(F.old_chat_member.status == 'member', F.new_chat_member.status == 'administrator')
async def bot_do_administrator(event: ChatMemberUpdated) -> None:
    chat = event.chat
    chat_id = chat.id
    chat_title = chat.title
    bot = event.bot
    promoted_by = event.from_user  # кто сделал бота админом
    
    # активируем группу
    await db.activate_group(chat_id)
    
    # Уведомляем того, кто назначил бота админом
    try:
        await bot.send_message(
            chat_id=promoted_by.id,
            text=f"*Бот активирован!* Начинаю следить за порядком в группе {chat_title}",
            parse_mode="Markdown"
        )
        print(f"Сообщение было отправлено пользователю {promoted_by.id}, который сделал бота админом!")
    except Exception as e:
        print(f"Сообщение не было отправлено пользователю {promoted_by.id}, который сделал бота админом! Ошибка: {e}")
    
    # Уведомление в группу
    await bot.send_message(
        chat_id=chat_id,
        text=f"*Бот активирован!* Начинаю следить за порядком в группе {chat_title}",
        parse_mode="Markdown"
    )


# Бота удалили из группы
@router.my_chat_member(F.new_chat_member.status == 'left')
async def bot_delete_from_group(event: ChatMemberUpdated) -> None:
    old = event.old_chat_member.status
    new = event.new_chat_member.status
    
    # Бота удалили из группы
    if old in ['member', 'administrator'] and new == 'left':
        chat = event.chat
        bot = event.bot
        removed_by = event.from_user
    
        # Уведомляем того, кто удалил бота
        try:
            await bot.send_message(
                chat_id=removed_by.id,
                text=f"Меня удалили из группы *{chat.title}*.\n\n"
                     f"Если передумаете — добавьте снова.",
                parse_mode="Markdown"
            )
            print(f"Сообщение было отправлено пользователю {removed_by.id}, который удалил бота из группы.")
        except Exception as e:
            print(f"Сообщение не было отправлено пользователю {removed_by.id}, который удалил бота из группы. Ошибка: {e}")
        
        await db.remove_group(event.chat.id)


# Бота лишили прав администратора
@router.my_chat_member(F.old_chat_member.status == 'administrator', F.new_chat_member.status == 'member')
async def bot_demoted(event: ChatMemberUpdated):
    chat = event.chat
    bot = event.bot
    demoted_by = event.from_user
    
    await db.deactivate_group(chat.id)
    
    # Уведомление тому, кто лишил прав (если есть)
    try:
        await bot.send_message(
            chat_id=demoted_by.id,
            text=f"Модерация отключена в группе *{chat.title}*.\n\n"
                 f"Вы отозвали права администратора.",
            parse_mode="Markdown"
        )
        print(f"Сообщение было отправлено пользователю {demoted_by.id}, который лишил прав администратора в группе.")
    except Exception:
        print(f"Сообщение не было отправлено пользователю {demoted_by.id}, который лишил прав администратора в группе. Ошибка: {e}")
   
    
# При исключении участника или при выходе участника удаляются все его данные
@router.chat_member()
async def member_status_changed(event: ChatMemberUpdated) -> None:
    old = event.old_chat_member.status
    new = event.new_chat_member.status
    
    # Получаем пользователя, чей статус изменился
    user = event.old_chat_member.user
    user_id = user.id
    chat = event.chat
    chat_id = chat.id
    
    # Пользователь вышел сам
    if old == 'member' and new == 'left':
        await db.remove_user(user_id, chat_id)
        print(f"Пользователь {user.first_name} вышел из группы {chat.title}")
    
    # Пользователя исключили (кикнули)
    elif new == 'kicked':
        await db.remove_user(user_id, chat_id)
        print(f"Пользователь {user.first_name} был исключён из группы {chat.title}")
        




