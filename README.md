# Workout Journal Backend

Отдельный backend-репозиторий для приложения журнала тренировок.

## Что уже есть

- FastAPI API
- PostgreSQL
- Dockerfile
- `docker-compose.yaml` для локальной разработки
- `docker-compose.server.yaml` для своего сервера
- GitHub Actions для сборки и публикации образа в GHCR
- JWT-авторизация
- вход по одноразовому коду из email
- sync endpoint для Flutter-клиента

## API

После запуска доступны:

- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/api/auth/register`
- `http://127.0.0.1:8000/api/auth/login`
- `http://127.0.0.1:8000/api/auth/request-code`
- `http://127.0.0.1:8000/api/auth/verify-code`
- `http://127.0.0.1:8000/api/sync`

## Локальный запуск без Docker

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Если `DATABASE_URL` не задан, backend использует SQLite в `data/app.db`.

## Локальный запуск через Docker

```powershell
docker compose up --build
```

После старта:

- API: `http://127.0.0.1:8000`
- Swagger: `http://127.0.0.1:8000/docs`
- Postgres: `localhost:5432`

## Что лежит в репозитории

- `Dockerfile` — сборка backend-контейнера
- `docker-compose.yaml` — локальная разработка
- `docker-compose.server.yaml` — запуск на своем сервере из GHCR-образа
- `.env.example` — пример env для локальной разработки
- `.env.server.example` — пример env для своего сервера
- `scripts/server-redeploy.sh` — обновление контейнеров на сервере

## GHCR и GitHub Actions

Workflow `.github/workflows/publish-ghcr.yml`:

1. собирает Docker-образ
2. пушит его в GitHub Container Registry
3. обновляет теги `latest`, `main` и `sha-*`

Итоговый образ:

```text
ghcr.io/mavravetasyan/workout-journal-backend:latest
```

## Запуск на своем сервере

### 1. Подготовить сервер

Нужно установить:

- Docker
- Docker Compose plugin

### 2. Скопировать backend-репозиторий на сервер

```bash
git clone https://github.com/MavrAvetasyan/workout-journal-backend.git
cd workout-journal-backend
```

### 3. Создать `.env.server`

Можно взять за основу `.env.server.example`.

Минимум нужно заполнить:

- `BACKEND_IMAGE`
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `SECRET_KEY`
- `CORS_ORIGINS`

### 4. Один раз войти в GHCR на сервере

```bash
echo <github_token> | docker login ghcr.io -u <github_username> --password-stdin
```

Токену обычно нужны права на чтение пакетов.

### 5. Запустить контейнеры

```bash
docker compose -f docker-compose.server.yaml up -d
```

### 6. Обновлять backend после новых пушей

```bash
./scripts/server-redeploy.sh
```

Этот скрипт:

1. подтягивает свежий образ из GHCR
2. перезапускает backend и postgres
3. чистит старые dangling images

## Переменные окружения

### Основные

- `DATABASE_URL`
- `SECRET_KEY`
- `CORS_ORIGINS`
- `STATIC_DIR`
- `MAIL_PROVIDER`
- `MAIL_FROM`
- `MAIL_REPLY_TO`
- `RESEND_API_KEY`
- `APP_NAME`
- `APP_LOGIN_URL`
- `LOGIN_CODE_TTL_MINUTES`
- `LOGIN_CODE_LENGTH`
- `LOGIN_CODE_RESEND_SECONDS`
- `LOGIN_CODE_MAX_ATTEMPTS`
- `DEBUG_AUTH_CODES`

### Для server compose

- `BACKEND_IMAGE`
- `BACKEND_PORT`
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`

## Что дальше

Следующие шаги по проекту:

1. подключить Flutter mobile к постоянному backend
2. подключить реальный почтовый домен и выключить `DEBUG_AUTH_CODES`
3. довести красивый production-шаблон письма под бренд
4. настроить автообновление на своем сервере
