from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def get_toxicity_check_keyboard(message_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Да", callback_data=f"confirm_{message_id}"),
            InlineKeyboardButton(text="Нет", callback_data=f"reject_{message_id}")
        ]
    ])