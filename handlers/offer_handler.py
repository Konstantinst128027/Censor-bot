import asyncio
import concurrent.futures
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
import database.requests as db
from model import solve_decision
from keyboards.chek_mess import get_toxicity_check_keyboard
from .model_handler import model
from aiogram.enums import ChatType



router = Router()

# Глобальный executor для модели, дополнительный рабочий поток
_executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)

# создаем дополнительный поток, чтобы он помогал нам быстрее работать
async def predict_toxicity(text: str) -> float:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(_executor, model.predict, text)


@router.message(F.chat.type !=ChatType.PRIVATE, F.text)
async def check_toxicity(message: Message) -> None:
    message_id = message.message_id
    chat_id = message.chat.id
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    chat_title = message.chat.title
    message_text = message.text
    bot = message.bot
    
    # Проверяем, активна ли группа
    if not await db.is_group_active(chat_id):
        return
    
    # Админов не проверяем
    try:
        member = await message.bot.get_chat_member(chat_id, user_id)
        if member.status in ['creator', 'administrator']:
            print("Сообщение администратора не проверяем:(")
            return
    except Exception:
        pass
    
    # Асинхронно проверяем токсичность
    probability = await predict_toxicity(message_text)
    decision = solve_decision(probability)
    if decision == 0:
        return 
    elif decision == 1:
        message_id = await db.save_message(user_id, message_text, probability, chat_title, chat_id, message_id)
        keyboard = get_toxicity_check_keyboard(message_id)


        admins = await bot.get_chat_administrators(chat_id)
    
        # Ищем создателя
        creator = None
        for admin in admins:
            if admin.status == 'creator':
                creator = admin.user.id
                break
    
        text = f"*Проверка сообщения!*\n\n"
        text += f"Пользователь: *{user_name}*\n"
        text += f"Сообщение: _{message_text}_\n\n"
        text += f"Вероятность токсичности: *{probability:.1%}*\n\n"
        text += f"По вашему мнению, это сообщение является токсичным?"
    
        if creator:
            try:
                await bot.send_message(chat_id=creator, text=text, reply_markup=keyboard, parse_mode="Markdown")
                print(f"Уведомление отправлено создателю {creator}") 
            except Exception as e:
                print(f"Не удалось отправить создателю: {e}")
        else:
            for admin in admins:
                if admin.status == 'administrator':
                    try:
                        await bot.send_message(chat_id=admin.user.id, text=text, reply_markup=keyboard, parse_mode="Markdown")
                        print(f"Уведомление отправлено администратору {admin.user.id}")
                    except Exception as e:
                        print(f"Не удалось отправить администратору: {e}")
    elif decision == 2:
        try:
            await message.delete()
            print(f"Сообщение удалено: {message_id}")
        except Exception as e:
            print(f"Не удалось удалить сообщение: {e}")
        

        warning_count = await db.add_warning(user_id, chat_id, user_name, chat_title)
        await db.save_message(user_id, message_text, probability, chat_title, chat_id, message_id)
        
        text = f"{user_name}, ваше сообщение удалено!\n\n"
        text += f"Ваше сообщение: _{message_text}_"
        text += f"Токсичность: {probability:.1%}\n"
        text += f"Предупреждение {warning_count}/5"

        try:
            await bot.send_message(chat_id = user_id, text=text, parse_mode="Markdown")
            print(f"Уведомление отправлено пользователю {user_id}")
        except Exception as e:
            print(f"Не удалось отправить пользователю: {e}")

        
        if warning_count >= 5:
            try:
                # Баним пользователя в группе
                await bot.ban_chat_member(chat_id, user_id)
        
                # Уведомление в группу
                await message.answer(f" {user_name} заблокирован за 5 нарушений!")
        
                # Личное уведомление пользователю
                try:
                    await bot.send_message(
                        chat_id=user_id,
                        text=f"*вы были заблокированы!*\n"
                            f"Вы получили 5 предупреждений в группе *{chat_title}*.\n"
                            f"Причина: систематическое нарушение правил (токсичные сообщения).\n\n"
                            f"Вы больше не можете писать в этой группе.\n\n"
                            f"*Что означает бан?*\n"
                            f"• Ваши сообщения будут удаляться\n"
                            f"• Вы не сможете писать в чате\n"
                            f"• Вы не сможете отвечать на сообщения\n\n"
                            f"Если считаете, что это ошибка — обратитесь к администраторам группы.",
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    print(f"Не удалось отправить уведомление пользователю {user_id}: {e}")
            
            except Exception as e:
                print(f"Не удалось забанить пользователя {user_id}: {e}")


# обработка кнопки 'Да'
@router.callback_query(F.data.startswith("confirm_"))
async def confirm_toxic(callback: CallbackQuery) -> None:
    await callback.answer()
    
    message_id = int(callback.data.split("_")[-1])
    message_data = await db.get_message_by_id(message_id)
    
    if not message_data:
        await callback.answer("Сообщение не найдено!", show_alert=True)
        return
    
    user_name = await db.get_user_name_by_id(message_data.user_id)
    if not user_name:
        user_name = "Пользователь"
    
    try:
        await callback.bot.delete_message(
            chat_id=message_data.chat_id,
            message_id=message_data.message_id
        )
    except Exception as e:
        print(f"Не удалось удалить сообщение: {e}")
    
    warning_count = await db.add_warning(
        user_id=message_data.user_id,
        group_id=message_data.chat_id,
        user_name=user_name,
        group_name=message_data.group_name
    )
    
    await callback.message.delete()
    
    text = f"{user_name}, ваше сообщение удалено!\n"
    text += f"Ваше сообщение: {message_data.message_text}\n"
    text += f"Токсичность: {message_data.probability:.1%}\n"
    text += f"Предупреждение {warning_count}/5"

    try:
        await callback.bot.send_message(
            chat_id=message_data.user_id,
            text=text
        )
    except Exception:
        pass
    
    if warning_count >= 5:
        try:
            await callback.bot.ban_chat_member(message_data.chat_id, message_data.user_id)
            await callback.bot.send_message(
                chat_id=message_data.chat_id,
                text=f"{user_name} заблокирован за 5 нарушений!"
            )
        except Exception as e:
            print(f"Не удалось забанить: {e}")
    
    # Бан после 5 предупреждений
    if warning_count >= 5:
            try:
                # Баним пользователя в группе
                await callback.bot.ban_chat_member(message_data.chat_id, message_data.user_id)
        
                # Уведомление в группу
                await callback.bot.send_message(
                    chat_id=message_data.chat_id,
                    text = f" {message_data.user_name} заблокирован за 5 нарушений!"
                    )
        
                # Личное уведомление пользователю
                try:
                    await callback.bot.send_message(
                        chat_id=message_data.user_id,
                        text=f"*вы были заблокированы!*\n"
                            f"Вы получили 5 предупреждения в группе *{message_data.group_name}*.\n"
                            f"Причина: систематическое нарушение правил (токсичные сообщения).\n\n"
                            f"Вы больше не можете писать в этой группе.\n\n"
                            f"*Что означает бан?*\n"
                            f"• Ваши сообщения будут удаляться\n"
                            f"• Вы не сможете писать в чате\n"
                            f"• Вы не сможете отвечать на сообщения\n\n"
                            f"Если считаете, что это ошибка — обратитесь к администраторам группы.",
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    print(f"Не удалось отправить уведомление пользователю {message_data.user_id}: {e}")
            
            except Exception as e:
                print(f"Не удалось забанить пользователя {message_data.user_id}: {e}")


@router.callback_query(F.data.startswith("reject_"))
async def confirm_not_toxic(callback: CallbackQuery) -> None:
    await callback.answer() 
    # Получаем ID сообщения
    message_id = int(callback.data.split("_")[-1])
    
    # Получаем данные сообщения
    message_data = await db.get_message_by_id(message_id)

    
    if not message_data:
        await callback.answer("Сообщение не найдено!", show_alert=True)
        return
    
    await db.delete_warning_message(message_id)

    # Удаляем сообщение с кнопкой у администратора
    await callback.message.delete()
    
    await callback.message.answer(
        text = f"Сообщение не будет удалено, оно прошло проверку токсичности.",
        parse_mode="Markdown"
    )
