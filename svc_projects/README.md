# svc_projects - Микросервис управления строительными проектами

## Описание

Микросервис для управления строительными проектами в системе управления дефектами. Предоставляет API для создания, чтения и обновления проектов с контролем доступа на основе ролей.

## Структура проекта

```
svc_projects/
├── alembic/               # Миграции базы данных
│   └── versions/
│       └── 0001_init_projects.py
├── api/                   # API слой
│   ├── deps.py           # Зависимости (auth, validation)
│   └── v1/
│       └── projects.py   # Роутеры проектов
├── core/                  # Ядро приложения
│   ├── auth.py           # JWT валидация
│   └── config.py         # Конфигурация (settings)
├── db/                    # База данных
│   └── database.py       # SQLAlchemy engine и session
├── models/                # SQLAlchemy модели
│   └── projects.py       # Модель Projects
├── schemas/               # Pydantic схемы
│   └── projects.py       # ProjectCreate, ProjectRead, ProjectUpdate
├── .env                   # Переменные окружения
├── main.py               # Точка входа FastAPI приложения
└── requirements.txt      # Python зависимости
```

## API Endpoints

### POST /api/v1/projects
**Создание проекта** (только MANAGER, ADMIN)

Request:
```json
{
  "name": "ЖК Новая Москва",
  "code": "NM-2024-01",
  "address": "г. Москва, ул. Ленина, 1",
  "customer_name": "ООО Застройщик",
  "stage": "CONSTRUCTION",
  "status": "ACTIVE",
  "manager_id": "uuid-менеджера",
  "start_date": "2024-01-15",
  "end_date": "2025-12-31"
}
```

Response:
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "name": "ЖК Новая Москва",
    ...
    "created_at": "2024-01-15T10:00:00",
    "updated_at": "2024-01-15T10:00:00"
  }
}
```

### GET /api/v1/projects
**Список проектов** (все роли, с фильтрацией по правам)

Query параметры:
- `skip` (int, default=0) - пропустить N записей
- `limit` (int, default=100, max=1000) - макс. количество записей
- `status` (ProjectStatus) - фильтр по статусу (ACTIVE/ON_HOLD/CLOSED)
- `stage` (ProjectStage) - фильтр по этапу (DESIGN/CONSTRUCTION/FINISHING/COMPLETED)
- `customer_name` (str) - фильтр по имени заказчика (частичное совпадение)
- `manager_id` (UUID) - фильтр по ID менеджера

**Права доступа:**
- MANAGER, ADMIN - видят все проекты
- SUPERVISOR, CUSTOMER - видят только проекты где manager_id == current_user.user_id

Response:
```json
{
  "success": true,
  "data": [
    {...},
    {...}
  ]
}
```

### GET /api/v1/projects/{project_id}
**Детали проекта** (все роли)

Response:
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "name": "...",
    ...
  }
}
```

### PATCH /api/v1/projects/{project_id}
**Обновление проекта** (только MANAGER, ADMIN)

Request (все поля опциональны):
```json
{
  "name": "Новое название",
  "status": "ON_HOLD",
  "stage": "FINISHING"
}
```

Response:
```json
{
  "success": true,
  "data": {...}
}
```

## Модели данных

### ProjectStage (Enum)
- `DESIGN` - Проектирование
- `CONSTRUCTION` - Строительство
- `FINISHING` - Отделка
- `COMPLETED` - Завершен

### ProjectStatus (Enum)
- `ACTIVE` - Активный
- `ON_HOLD` - Приостановлен
- `CLOSED` - Закрыт

### Projects (SQLAlchemy Model)
| Поле | Тип | Описание |
|------|-----|----------|
| id | UUID | Первичный ключ |
| name | String(255) | Название проекта |
| code | String(50) | Уникальный код проекта (опционально) |
| address | String(255) | Адрес объекта |
| customer_name | String(255) | Имя заказчика |
| stage | ProjectStage | Этап проекта |
| status | ProjectStatus | Статус проекта |
| manager_id | UUID | ID менеджера проекта (индексированное поле) |
| start_date | Date | Дата начала (опционально) |
| end_date | Date | Дата окончания (опционально) |
| created_at | DateTime | Дата создания |
| updated_at | DateTime | Дата обновления |

## Запуск сервиса

### 1. Установка зависимостей

```bash
cd /Users/nihihitik/Projects/microservices-frameworks/svc_projects
pip install -r requirements.txt
```

### 2. Настройка переменных окружения

Файл `.env` должен содержать следующие параметры:

```env
# Database Configuration
DB_USER=projects_user
DB_PASSWORD=SecurePass2024Projects
DB_HOST=localhost
DB_PORT=5434
DB_NAME=projects_db

# Database URL (constructed from above)
DATABASE_URL=postgresql://projects_user:SecurePass2024Projects@localhost:5434/projects_db

# Application Configuration
APP_HOST=0.0.0.0
APP_PORT=8002

# Auth Service URL (for validation)
AUTH_SERVICE_URL=http://localhost:8001

# JWT Configuration (must match svc_auth for token validation)
JWT_SECRET_KEY=your_super_secret_jwt_key_9f7d3e2c1b5a8f4g6h9j0k2m5n7p9q1r
JWT_ALGORITHM=HS256
```

**ВАЖНО:**
- PostgreSQL база данных `projects_db` должна быть создана в Docker
- Пользователь `projects_user` должен существовать и иметь права на `projects_db`
- `JWT_SECRET_KEY` **ОБЯЗАТЕЛЬНО** должен совпадать с ключом в `svc_auth`
- Порт `DB_PORT=5434` используется для Docker контейнера (внутренний порт 5432 маппится на 5434)
- Пароль `DB_PASSWORD` должен совпадать с паролем в `DATABASE_URL` и Docker Compose конфигурации

### 3. Применение миграций

```bash
alembic upgrade head
```

### 4. Запуск сервиса

```bash
# Вариант 1: через uvicorn напрямую
uvicorn main:app --reload --host 0.0.0.0 --port 8002

# Вариант 2: через python (использует настройки из .env)
python main.py
```

Сервис будет доступен по адресу: `http://localhost:8002`

### 5. Документация API

После запуска:
- Swagger UI: http://localhost:8002/docs
- ReDoc: http://localhost:8002/redoc
- OpenAPI JSON: http://localhost:8002/openapi.json

## Интеграция с другими сервисами

### svc_auth
Сервис projects обращается к svc_auth для:
- Валидации JWT токенов (через `decode_access_token`)
- Проверки существования пользователей (через `validate_manager_exists`)

Убедитесь, что `svc_auth` запущен на `http://localhost:8001` перед запуском `svc_projects`.

### svc_gateway
Gateway должен проксировать запросы:
```
/api/v1/projects/** → http://svc_projects:8002/api/v1/projects/**
```

## Бизнес-правила

1. **Создание проектов**: Доступно только MANAGER и ADMIN
2. **Обновление проектов**: Доступно только MANAGER и ADMIN
3. **Просмотр проектов**:
   - MANAGER/ADMIN видят все проекты
   - SUPERVISOR/CUSTOMER видят только свои проекты (where manager_id = current_user_id)
4. **Валидация manager_id**: При создании/обновлении обязательно проверяется существование пользователя через HTTP запрос к svc_auth
5. **Уникальность code**: Если указан code, он должен быть уникальным в системе
6. **Переходы статусов**: Нет ограничений на переходы (CLOSED можно вернуть в ACTIVE)
7. **Переходы этапов**: Нет ограничений на переходы (можно менять в любом направлении)

## Формат ответов

Все эндпоинты возвращают единый формат:

**Успех:**
```json
{
  "success": true,
  "data": {...}
}
```

**Ошибка:**
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message",
    "details": [...]  // для валидационных ошибок
  }
}
```

## Коды ошибок

- `400 BAD_REQUEST` - Некорректные данные (например, дублирующийся code)
- `401 UNAUTHORIZED` - Невалидный или истекший токен
- `403 FORBIDDEN` - Недостаточно прав (неправильная роль)
- `404 NOT_FOUND` - Проект или пользователь не найден
- `422 VALIDATION_ERROR` - Ошибка валидации Pydantic
- `500 INTERNAL_SERVER_ERROR` - Внутренняя ошибка сервера
- `503 SERVICE_UNAVAILABLE` - Сервис auth недоступен

## Примеры использования

### Создание проекта (требуется токен MANAGER/ADMIN)

```bash
curl -X POST http://localhost:8002/api/v1/projects \
  -H "Authorization: Bearer <jwt-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "ЖК Солнечный",
    "code": "SUN-2024",
    "address": "г. Москва, ул. Солнечная, 10",
    "customer_name": "ООО Солнце",
    "stage": "DESIGN",
    "status": "ACTIVE",
    "manager_id": "uuid-менеджера",
    "start_date": "2024-02-01"
  }'
```

### Получение списка проектов

```bash
curl http://localhost:8002/api/v1/projects?status=ACTIVE&limit=50 \
  -H "Authorization: Bearer <jwt-token>"
```

### Обновление проекта

```bash
curl -X PATCH http://localhost:8002/api/v1/projects/{project_id} \
  -H "Authorization: Bearer <jwt-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "ON_HOLD",
    "stage": "CONSTRUCTION"
  }'
```

## Разработка

### Проверка типов
```bash
mypy .
```

### Форматирование кода
```bash
black .
ruff check .
```

### Тестирование
```bash
pytest
pytest --cov=. --cov-report=html
```

## Технический стек

- **FastAPI** 0.110+ - Web framework
- **SQLAlchemy** 2.x - ORM
- **Alembic** - Database migrations
- **Pydantic** v2 - Data validation
- **PostgreSQL** - Database
- **PyJWT** - JWT token handling
- **httpx** - Async HTTP client
- **uvicorn** - ASGI server

## Лицензия

Проект разработан для внутреннего использования в системе управления дефектами строительных объектов.
