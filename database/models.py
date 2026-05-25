import os
from dotenv import load_dotenv

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

load_dotenv()

engine = create_async_engine(url=os.getenv("DB_URL"))  # создает базу данных
async_session = async_sessionmaker(engine)
Base = declarative_base() # метакласс для создания таблиц в базе данных через SQLalchemy

class ActiveGroup(Base):
    __tablename__ = 'active_groups'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(Integer, unique=True, nullable=False)
    group_name = Column(String(255))
    is_active = Column(Boolean, default=False)
    
    # Связь с пользователями
    users = relationship("UserWarning", back_populates="group", cascade="all, delete-orphan")


class UserWarning(Base):
    __tablename__ = 'user_warnings'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    user_name = Column(String(255))
    group_id = Column(Integer, ForeignKey('active_groups.id', ondelete="CASCADE"))
    group_name = Column(String(255))
    warning_count = Column(Integer, default=0)
    
    # Связь с группой
    group = relationship("ActiveGroup", back_populates="users")
    


class WarningMessage(Base):
    __tablename__ = 'warning_messages'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('user_warnings.id', ondelete="CASCADE"))
    message_id = Column(Integer)
    chat_id = Column(Integer)
    message_text = Column(Text)
    probability = Column(Float)
    group_name = Column(String(255))
    user_name = Column(String(255))


async def init_db():
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
