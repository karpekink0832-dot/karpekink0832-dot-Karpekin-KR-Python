from fastapi.params import Depends
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.db import User, get_session, Course, Material, Progress


async def get_user_by_name(username:str, session:AsyncSession=Depends(get_session)):

    query=select(User).where(User.name==username)
    result=await session.execute(query)
    user=result.scalar_one_or_none()
    return user

async def get_user_by_id(id:int, session:AsyncSession=Depends(get_session)):

    query=select(User).where(User.id==id)
    result=await session.execute(query)
    user=result.scalar_one_or_none()
    return user

async def get_course_by_id(course_id:int, session:AsyncSession=Depends(get_session)):
    query = select(Course).where(Course.id == course_id)
    result = await session.execute(query)
    course = result.scalar_one_or_none()
    return course

async def get_material_by_counter(course_id:int, material_counter:int, session:AsyncSession=Depends(get_session)):
    query = select(Material).where(and_(Material.course_id == course_id, Material.counter==material_counter))
    result = await session.execute(query)
    material = result.scalar_one_or_none()
    return material

async def get_max_counter_by_course(course_id:int, session:AsyncSession=Depends(get_session)):
    query = select(func.max(Material.counter)).where(Material.course_id == course_id)
    result = await session.execute(query)
    material = result.scalar_one_or_none()
    return material

async def get_progress_user_material(user_id: int, material_id: int, session:AsyncSession=Depends(get_session)):
    query = select(Progress).where(and_(Progress.user_id == user_id, Progress.material_id == material_id))
    result = await session.execute(query)
    progress = result.scalar_one_or_none()
    return progress




