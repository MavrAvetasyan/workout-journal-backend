# Workout Journal Backend

Отдельный backend-репозиторий для приложения журнала тренировок.

## Стек

- Python 3.12
- FastAPI
- SQLAlchemy
- PostgreSQL
- Docker / Docker Compose

## Что внутри

- регистрация и логин
- профиль текущего пользователя
- CRUD для упражнений
- CRUD для замеров
- CRUD для тренировок
- полный sync-эндпоинт для клиента
- healthcheck

## Локальный запуск без Docker

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

API будет доступен на:

- `http://127.0.0.1:8000`
- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/health`

По умолчанию без переменной `DATABASE_URL` используется SQLite в `data/app.db`.

## Docker Compose

```powershell
docker compose up --build
```

После старта:

- API: `http://127.0.0.1:8000`
- Swagger: `http://127.0.0.1:8000/docs`
- Postgres: `localhost:5432`

## Переменные окружения

- `DATABASE_URL`
- `SECRET_KEY`
- `STATIC_DIR` — опционально, если нужно раздавать отдельную статику

## GHCR

В репозитории есть GitHub Actions workflow, который:

- собирает Docker-образ
- публикует его в GitHub Container Registry

Образ будет доступен по пути вида:

`ghcr.io/<owner>/workout-journal-backend`
