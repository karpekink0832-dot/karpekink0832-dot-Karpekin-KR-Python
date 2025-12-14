from datetime import datetime

from sqlalchemy import Integer, String, Boolean, ForeignKey, Text, Date
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


engine = create_async_engine(f"sqlite+aiosqlite:///database/database.db")

session_maker=async_sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
   __abstract__=True #чтобы не создавалась таблица в бд для этого класса


class User(Base):
    __tablename__ = 'Users'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True)
    hashed_password: Mapped[str] = mapped_column(String)

    courses:Mapped[list['Course']]=relationship('Course', back_populates='owner', cascade='all, delete-orphan')
    progress: Mapped[list['Progress']] = relationship('Progress', back_populates='user', cascade='all, delete-orphan')

class Course(Base):
    __tablename__ = 'Courses'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text)
    owner_id: Mapped[int] = mapped_column(Integer, ForeignKey('Users.id'))
#    date_start: Mapped[datetime.date] = mapped_column(Date)
#    date_end: Mapped[datetime.date] = mapped_column(Date)

    owner:Mapped['User']=relationship('User', back_populates='courses')
    materials: Mapped[list['Material']] = relationship('Material', back_populates='course', cascade='all, delete-orphan')


class Material(Base):
    __tablename__ = 'Materials'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String)
    content: Mapped[str] = mapped_column(Text)
    course_id: Mapped[int] = mapped_column(Integer, ForeignKey('Courses.id'))
    date_lesson: Mapped[datetime.date] = mapped_column(Date)
    counter:Mapped[int]=mapped_column(Integer, default=1)

    course: Mapped['Course'] = relationship('Course', back_populates='materials')
    progress: Mapped['Progress'] = relationship('Progress', back_populates='material', cascade='all, delete-orphan')

class Progress(Base):
    __tablename__ = 'Progress'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('Users.id'))
    material_id: Mapped[int] = mapped_column(Integer, ForeignKey('Materials.id'))
    completed: Mapped[bool] = mapped_column(Boolean)

    material: Mapped['Material'] = relationship('Material', back_populates='progress')
    user: Mapped['User'] = relationship('User', back_populates='progress')



async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_session():
    async with session_maker() as session:
        yield session

