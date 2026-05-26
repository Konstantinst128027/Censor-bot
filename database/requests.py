from sqlalchemy import select, update, delete
from .models import UserWarning, WarningMessage, Group, async_session

# добавляем группу в таблицу и активируем ее. Если же она была уже в таблице смотрим не изменился ли ее id если да, то меняем id
async def add_group(group_id: int, group_name: str) -> None:
    async with async_session() as session:
        async with session.begin():
            # Удаляем старые записи с таким же названием
            await session.execute(
                delete(Group).where(Group.group_name == group_name)
            )
            # Добавляем новую
            session.add(Group(
                group_id=group_id,
                group_name=group_name,
                is_active=False
            ))


#получаем группу по group_id
async def get_group_by_id(group_id: int):
    async with async_session() as session:
        result = await session.execute(
            select(Group).where(Group.group_id == group_id)
        )
        return result.scalar_one_or_none()

# Получае список всех групп
async def get_all_groups():
    async with async_session() as session:
        result = await session.execute(select(Group))
        return result.scalars().all()


# активируем группу         
async def activate_group(group_id: int) -> None:
    async with async_session() as session:
        async with session.begin():
            await session.execute(
                update(Group)
                .where(Group.group_id == group_id)
                .values(is_active=True)
            )


# деактивируем группу         
async def deactivate_group(group_id: int) -> None:
    async with async_session() as session:
        async with session.begin():
            await session.execute(
                update(Group)
                .where(Group.group_id == group_id)
                .values(is_active=False)
            )


# Удаляем группу из бд, если бота исключили из группы
async def remove_group(group_id: int) -> None:
    async with async_session() as session:
        async with session.begin():
            # Находим группу
            result = await session.execute(
                select(Group).where(Group.group_id == group_id)
            )
            group = result.scalar_one_or_none()
            
            if group:
                # Удаляем всех пользователей этой группы
                await session.execute(
                    delete(UserWarning).where(UserWarning.group_id == group.id)
                )
                # Удаляем группу
                await session.delete(group)


# Удаляем пользователя и его сообщения из базы данных
async def remove_user(user_id: int, group_id: int) -> None:
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(
                select(UserWarning).where(
                    UserWarning.user_id == user_id,
                    UserWarning.group_id == group_id
                )
            )
            user = result.scalar_one_or_none()
            
            if user:
                await session.execute(
                    delete(WarningMessage).where(
                        WarningMessage.user_id == user.id,
                        WarningMessage.chat_id == group_id
                    )
                )
                await session.delete(user)


# активна ли группа или нет
async def is_group_active(chat_id: int) -> bool:
    async with async_session() as session:
        result = await session.execute(
            select(Group.is_active).where(Group.group_id == chat_id)
        )
        is_active = result.scalar_one_or_none()
        return is_active
    

# Сохраняет сообщение
async def save_message(user_id: int, message_text: str, probability: float, group_name: str, chat_id: int, message_id: int) -> int:
    async with async_session() as session:
        async with session.begin():
            message = WarningMessage(
                user_id=user_id,
                message_text=message_text,
                probability=probability,
                chat_id = chat_id,
                group_name = group_name,
                message_id = message_id
            )
            session.add(message)
            await session.flush() # чтобы получить id то коммита
            print(f"Собобщение {message_text} от пользователя {user_id} было сохранено!")
            return message.id


# добавляет пользователя в таблицу с пользователями, а если такой пользователь уже есть, то просто добавляет к его warning_count +1
async def add_warning(user_id: int, group_id: int, user_name: str, group_name: str) -> int:
    async with async_session() as session:
        async with session.begin():
            # Ищем пользователя
            result = await session.execute(
                select(UserWarning).where(
                    UserWarning.user_id == user_id,
                    UserWarning.group_id == group_id
                )
            )
            user = result.scalar_one_or_none()
            
            if user:
                user.warning_count += 1
                warning_count = user.warning_count
            else:
                user = UserWarning(
                    user_id=user_id,
                    group_id=group_id,
                    user_name=user_name,
                    group_name = group_name,
                    warning_count=1
                )
                session.add(user)
                warning_count = 1
            
            return warning_count


# получаем сообщение по message_id
async def get_message_by_id(message_id: int) -> WarningMessage | None:
    async with async_session() as session:
        result = await session.execute(
            select(WarningMessage).where(WarningMessage.id == message_id)
        )
        return result.scalar_one_or_none()


# получаем имя пользователя по user_id 
async def get_user_name_by_id(user_id: int) -> str | None:
    async with async_session() as session:
        result = await session.execute(
            select(UserWarning.user_name).where(UserWarning.user_id == user_id)
        )
        return result.scalar_one_or_none()


# удаляет сообщение по message_id
async def delete_warning_message(message_id: int) -> None:
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(
                delete(WarningMessage).where(
                    WarningMessage.id == message_id
                )
            )
            print("Сообщение было удалено из базы данных!")

    
    