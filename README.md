# Сервис учета учебных курсов

API для учета учебных курсов: расписание, прогресс, материалы. (
FastAPI 
async SQLAlchemy 
JWT
bcrypt
Документация Swagger: `/docs`

## Запуск локально
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
База создается автоматически в файле `database.db`. Переменные окружения:
- `DATABASE_URL` — строка подключения (по умолчанию `sqlite+aiosqlite:///database/database.db`)

## Пример использования
1. `POST /register` — регистрация (JSON: `name`, `password`).
2. `POST /login` — получить JWT токен (форма `username`, `password`).
3. Для перехода на защищенные эндпоинты использовать JWT токен. Ввести в заголовок: `Authorization: Bearer <token>`.

### CRUD
- `POST /add_course` — создать курс (title, description)
- `GET /courses`, `GET /courses/{id}`, `PUT/DELETE /courses/{id}`
- `GET /materials`, `GET /courses/{course_id}/{material_counter}`, `PUT/DELETE /courses/{course_id}/{material_counter}`
- `POST /courses/{course_id}` — добавить материал на курс (название, содержание, дата проведения занятия)
- `POST /courses/{course_id}/{material_counter}` - добавить отметку прогресса
- `GET /progress/{course_id}`
- `GET /schedule/{course_id}`
- `GET /user/{id}`, `DELETE /user/{id}` 
