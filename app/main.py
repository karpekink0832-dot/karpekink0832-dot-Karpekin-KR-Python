from contextlib import asynccontextmanager

import uvicorn

from fastapi import FastAPI, HTTPException, status
from fastapi.params import Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select,  and_

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import get_course_by_id, get_material_by_counter, get_max_counter_by_course, get_progress_user_material, \
    get_user_by_id
from app.models import MaterialCreate, MaterialResponse, ProgressResponse, CourseUpdate, MaterialUpdate
from app.auth import get_password_hash, get_current_user, authentificate_user, create_token
from app.crud import get_user_by_name
from app.models import UserResponse, UserCreate, CourseCreate, CourseResponse
from app.database.db import create_tables, User, get_session, Course, Material, Progress


@asynccontextmanager
async def lifespan(app: FastAPI):

    await create_tables()
    yield


app=FastAPI(lifespan=lifespan)


@app.get('/')
async def root():
    return 'Сервис учета учебных курсов - Расписание, прогресс, материалы'


@app.post('/register', response_model=UserResponse, tags=['registration/auth'], summary='Регистрация', description='Post для регистрации. Принимает логин(str) и пароль(str)')
async def register(user_data: UserCreate, db:AsyncSession=Depends(get_session)):
    db_user=await get_user_by_name(user_data.name, db)
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Уже зарегестрирован')

    try:
        user=User(
        name=user_data.name,
        hashed_password = get_password_hash(user_data.password))

        db.add(user)
        await db.commit()
        await db.refresh(user)

        return UserResponse.model_validate(user)

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@app.post('/login', tags=['registration/auth'], summary='Получить токен', description='Post для получения jwt токена. Принимает логин(str) и пароль(str)')
async def login_for_token(form_data: OAuth2PasswordRequestForm=Depends(), session:AsyncSession=Depends(get_session)):
    user=await authentificate_user(session, form_data.username, form_data.password)

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Неверный логн или пароль')


    token=create_token({'sub':user.name})
    return {'access_token':token, 'token_type':'bearer', 'id':user.id, 'name':user.name}

@app.post('/add_course', tags=['course'], summary='Создать курс', description='Post для создания курса. Принимает название(str), описание(str). Требуется аутентификация')
async def add_course(course_data: CourseCreate, cur_user: UserResponse=Depends(get_current_user), db:AsyncSession=Depends(get_session)):
    try:
        course=Course(
            title=course_data.title,
            description=course_data.description,
            owner_id=cur_user.id)

        db.add(course)
        await db.commit()
        await db.refresh(course)

        res = CourseResponse.model_validate(course)
        res.owner_name=cur_user.name
        return res
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.get('/courses', tags=['course'], summary='Показать курсы', description='Get для получения всех курсов')
async def show_courses(session:AsyncSession=Depends(get_session)):

    query=select(Course)
    result = await session.execute(query)

    courses_select = result.scalars().all()
    CourseResponse_list=[]
    for i in courses_select:
        owner=await get_user_by_id(i.owner_id, session)
        owner=owner.name
        res = CourseResponse.model_validate(i)
        res.owner_name = owner

        CourseResponse_list.append(res)

    return CourseResponse_list

@app.post('/courses/{course_id}', tags=['material'], summary='Создать материал', description='Post для создания материала(статьи). Принимает название(str), содержание(str). Требуется аутентификация')
async def add_material(course_id:int, material_data: MaterialCreate, cur_user: UserResponse=Depends(get_current_user), db:AsyncSession=Depends(get_session)):
    course=await get_course_by_id(course_id, db)

    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Курс с таким id не найден')
    if cur_user.id!=course.owner_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Это не ваш курс')

    try:
        counter = await get_max_counter_by_course(course_id, db)
        if not counter:
            counter=1
        else:
            counter+=1

        material=Material(
            title=material_data.title,
            content=material_data.content,
            date_lesson=material_data.date_lesson,
            course_id=course_id,
            counter=counter
        )

        db.add(material)
        await db.commit()
        await db.refresh(material)

        return MaterialResponse.model_validate(material)

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.get('/courses/{course_id}', tags=['course'], summary='Информация о курсе', description='Get для получения информации о курсе и материалов курса. Требуется аутентификация')
async def course_info(course_id:int, session:AsyncSession=Depends(get_session)):
    course = await get_course_by_id(course_id, session)
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Курс с таким id не найден')

    response_info = {}
    response_info['course_info'] = course

    query = select(Material).where(Material.course_id==course.id)
    result = await session.execute(query)

    materials_select = result.scalars().all()
    response_info['materials']= materials_select
    return response_info


@app.get('/courses/{course_id}/{material_counter}', tags=['material'], summary='Информация о материале', description='Get для получения информации о материале по id курса и порядковому номеру материала. Требуется аутентификация')
async def material_info(course_id:int, material_counter:int, cur_user: UserResponse=Depends(get_current_user), session:AsyncSession=Depends(get_session)):
    course = await get_course_by_id(course_id, session)
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Курс с таким id не найден')

    material=await get_material_by_counter(course_id, material_counter, session)
    if not material:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Материал не найден')


    return MaterialResponse.model_validate(material)

@app.post('/courses/{course_id}/{material_counter}', tags=['progress'], summary='Отметить прогресс', description='Post для отметки прогресса для данного пользователя и конкретного материала. Требуется аутентификация')
async def set_progress(course_id:int, material_counter:int, cur_user: UserResponse=Depends(get_current_user), session:AsyncSession=Depends(get_session)):
    course = await get_course_by_id(course_id, session)
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Курс с таким id не найден')

    material=await get_material_by_counter(course_id, material_counter, session)
    if not material:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Материал не найден')

    progress_for_check=await get_progress_user_material(cur_user.id, material.id, session)
    if progress_for_check:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Прогресс для этого пользователя и материала уже отмечен')
    try:
        progress=Progress(
            user_id=cur_user.id,
            material_id=material.id,
            completed=True
        )


        session.add(progress)
        await session.commit()
        await session.refresh(progress)

        return ProgressResponse.model_validate(progress)

    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@app.put('/courses/{course_id}', tags=['course'], summary='Изменить курс', description='Put для Изменения курса. Можно изменить название(str), описание(str). Требуется аутентификация')
async def update_course(course_id:int, course_data: CourseUpdate, cur_user: UserResponse=Depends(get_current_user), session:AsyncSession=Depends(get_session)):
    course=await get_course_by_id(course_id, session)

    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Курс с таким id не найден')
    if cur_user.id != course.owner_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Это не ваш курс')

    try:
        query = select(Course).where(Course.id == course_id)
        result = await session.execute(query)
        course = result.scalar_one_or_none()
        for key, value in course_data:
            if value is not None:
                setattr(course, key, value)

        await session.commit()
        await session.refresh(course)
        course=CourseResponse.model_validate(course)
        owner = await get_user_by_id(course.owner_id, session)
        owner = owner.name
        course.owner_name = owner


        return course
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@app.get('/materials', tags=['material'], summary='Материалы', description='Get для получения информации о существующих материалах')
async def show_materials(session:AsyncSession=Depends(get_session)):

    query=select(Material)
    result = await session.execute(query)

    materials_select = result.scalars().all()
    MaterialResponse_list=[]
    for i in materials_select:
        MaterialResponse_list.append(MaterialResponse.model_validate(i))

    return MaterialResponse_list

@app.delete('/courses/{course_id}', tags=['course'], summary='Удалить курс', description='Delete для удаления курса. Удаляет материалы и отметки прогресса. Требуется аутентификация')
async def delete_course(course_id:int, cur_user: UserResponse=Depends(get_current_user), session:AsyncSession=Depends(get_session)):
    course=await get_course_by_id(course_id, session)

    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Курс с таким id не найден')
    if cur_user.id != course.owner_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Это не ваш курс')

    try:
        query = select(Course).where(Course.id == course_id)
        result = await session.execute(query)
        course = result.scalar_one_or_none()
        await session.delete(course)

        await session.commit()

        return {'status': 'Успешное удаление'}
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.delete('/courses/{course_id}/{material_counter}', tags=['material'], summary='Удалить материал', description='Delete для удаления материала. Удаляет отметки прогресса. Требуется аутентификация')
async def delete_material(course_id:int, material_counter: int, cur_user: UserResponse=Depends(get_current_user), session:AsyncSession=Depends(get_session)):
    course=await get_course_by_id(course_id, session)


    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Курс с таким id не найден')
    material = await get_material_by_counter(course_id, material_counter, session)
    if not material:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Материал не найден')
    if cur_user.id != course.owner_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Это не ваш курс')

    try:
        query = select(Material).where(Material.id == material.id)
        result = await session.execute(query)
        material = result.scalar_one_or_none()
        await session.delete(material)

        await session.commit()

        return {'status': 'Успешное удаление'}
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.delete('/user/{user_id}', tags=['user'], summary='Удалить пользователя', description='Delete для удаления пользователя. Удаляет курсы, созданные пользователем, их материалы и отметки прогресса. Требуется аутентификация')
async def delete_user(user_id:int, cur_user: UserResponse=Depends(get_current_user), session:AsyncSession=Depends(get_session)):

    if cur_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Вы не можете удалить чужой аккаунт')

    try:
        query = select(User).where(User.id == user_id)
        result = await session.execute(query)
        user = result.scalar_one_or_none()
        await session.delete(user)

        await session.commit()

        return {'status': 'Успешное удаление'}
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.get('/progress/{course_id}', tags=['progress'], summary='Прогресс по курсу', description='Get для просмотра прогресса пользователя по курсу. Требуется аутентификация')
async def course_progress(course_id:int,  cur_user: UserResponse=Depends(get_current_user), session:AsyncSession=Depends(get_session)):

    course = await get_course_by_id(course_id, session)
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Курс с таким id не найден')

    query = select(Material.id).where(Material.course_id == course_id)
    result = await session.execute(query)
    material_ids = result.scalars().all()

    if len(material_ids) == 0:
        return {'Message': 'В данном курсе пока нет занятий'}

    query = select(Progress).where(and_(Progress.material_id.in_(material_ids), Progress.user_id == cur_user.id))
    result = await session.execute(query)
    progress_select = result.scalars().all()

    return {'Message': f'Пройдено {len(progress_select)} из {len(material_ids)} занятий'}

@app.get('/schedule/{course_id}', tags=['course'], summary='Расписание курса', description='Get для получения расписания занятий курса с названием соответствующих материалов. Требуется аутентификация')
async def course_schedule(course_id:int, session:AsyncSession=Depends(get_session)):

    course = await get_course_by_id(course_id, session)
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Курс с таким id не найден')

    query = select(Material.title, Material.date_lesson).where(Material.course_id == course_id).order_by(Material.date_lesson)
    result = await session.execute(query)
    materials = result.all()

    if len(materials) == 0:
        return {'Message': 'В данном курсе пока нет занятий'}

    return [{'title':title, 'date_lesson':date_lesson} for title, date_lesson in materials]

@app.put('/courses/{course_id}/{material_counter}', tags=['material'], summary='Изменить материал', description='Post для изменения материала курса. Можно изменить название, содержание, дату проведения занятия. Требуется аутентификация')
async def update_material(course_id:int, material_counter:int, material_data: MaterialUpdate, cur_user: UserResponse=Depends(get_current_user), session:AsyncSession=Depends(get_session)):
    course=await get_course_by_id(course_id, session)

    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Курс с таким id не найден')
    material = await get_material_by_counter(course_id, material_counter, session)
    if not material:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Материал не найден')
    if cur_user.id != course.owner_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Это не ваш курс')


    try:
        query = select(Material).where(and_(Material.course_id == course_id, Material.counter==material_counter))
        result = await session.execute(query)
        material = result.scalar_one_or_none()
        for key, value in material_data:
            if value is not None:
                setattr(material, key, value)

        await session.commit()
        await session.refresh(material)

        return MaterialResponse.model_validate(material)
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.get('/user/{user_id}', tags=['user'], summary='Информация о пользователе', description='Get для получения курсов, созданных пользователем')
async def user_courses(user_id: int, session:AsyncSession=Depends(get_session)):

    query = select(User).where(User.id == user_id)
    result = await session.execute(query)
    user=result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Пользователь не найден')
    query=select(Course).where(Course.owner_id==user_id)
    result = await session.execute(query)
    courses = result.scalars().all()


    return {'username': user.name, 'user_id':user.id, 'courses':courses}


if __name__ == '__main__':
    uvicorn.run(app)
