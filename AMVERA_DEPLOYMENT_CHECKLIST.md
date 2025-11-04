# ✅ Полный Чеклист Развёртывания на Amvera

Используйте этот документ как пошаговый путь к успешному развёртыванию приложения на платформе Amvera.

---

## 📋 ЧТО ВЫ ДОЛЖНЫ ЗНАТЬ ПЕРЕД НАЧАЛОМ

### Архитектура вашего приложения:

```
Приложение состоит из 3 компонентов:

1. Frontend (React)
   - Порт: 3000 (или 80 в Nginx)
   - Путь Dockerfile: frontend/Dockerfile
   - Доступен по адресу: https://reyting.amvera.ru

2. Backend (FastAPI)
   - Порт: 8000
   - Путь Dockerfile: backend/Dockerfile
   - Доступен по адресу: https://api.reyting.amvera.ru

3. Database (PostgreSQL)
   - Хост: amvera-alex1976-cnpq-reyting-mo-rw
   - Порт: 5432
   - БД: reytingdb
   - Пользователь: reyting_user
   - УЖЕ СОЗДАНА на Amvera ✓
```

### Что находится на GitHub:

Repository: https://github.com/Aleksey341/Reyting

```
├── backend/
│   ├── Dockerfile          ← Для сборки backend контейнера
│   ├── amvera.yml          ← Конфигурация для Amvera (подробная)
│   ├── main.py             ← FastAPI приложение
│   ├── config.py           ← Конфигурация с Amvera параметрами
│   ├── models.py           ← ORM модели (SQLAlchemy)
│   ├── database.py         ← Подключение к БД
│   ├── routes/             ← API endpoints
│   └── requirements.txt     ← Python зависимости
│
├── frontend/
│   ├── Dockerfile          ← Для сборки frontend контейнера
│   ├── amvera.yml          ← Конфигурация для Amvera
│   ├── package.json        ← Node.js зависимости
│   ├── src/
│   │   ├── App.jsx         ← Главная React компонента
│   │   ├── pages/          ← Страницы приложения
│   │   ├── components/     ← Переиспользуемые компоненты
│   │   └── services/       ← API клиент
│   └── public/             ← Статические файлы
│
├── database_schema.sql     ← Миграция БД (НАДО ЗАПУСТИТЬ)
├── amvera.yml              ← Конфигурация root (для всего вместе)
│
├── AMVERA_CONFIGURATION_GUIDE.md      ← ШАГ 1: Что выбирать в форме
├── AMVERA_CONFIGURATION.md            ← Подробное объяснение параметров
├── AMVERA_DEPLOY.md                   ← Варианты развёртывания
├── AMVERA_SETUP.md                    ← Настройка БД
├── AMVERA_DEPLOYMENT_CHECKLIST.md     ← ВЫ ЗДЕСЬ (этот файл)
│
└── README.md               ← Общая информация о проекте
```

---

## 🚀 ПОШАГОВОЕ РУКОВОДСТВО РАЗВЁРТЫВАНИЯ

### ЭТАП 1: Подготовка (5 минут)

#### Шаг 1.1: Убедитесь что у вас есть доступ к Amvera

- [ ] У вас есть аккаунт на Amvera (https://console.amvera.ru)
- [ ] Вы можете войти в консоль
- [ ] У вас есть PostgreSQL база данных:
  - Хост: `amvera-alex1976-cnpq-reyting-mo-rw`
  - БД: `reytingdb`
  - Пользователь: `reyting_user`
  - Пароль: У вас должен быть свой пароль

#### Шаг 1.2: Получите пароль от БД

Если вы не знаете пароль от `reyting_user`:

1. Откройте https://console.amvera.ru
2. Перейдите в раздел **Database** или **PostgreSQL**
3. Найдите базу данных `reytingdb`
4. Нажмите на неё → **Settings** → **Users**
5. Найдите `reyting_user` и скопируйте пароль (или установите новый)

Запомните этот пароль - он нужен будет на Шаге 2.4!

#### Шаг 1.3: Инициализируйте базу данных

Вам нужно создать таблицы и заполнить справочные данные.

**Вариант A: Через pgAdmin (графический интерфейс)**

1. Откройте https://console.amvera.ru
2. Найдите свою БД → нажмите **pgAdmin** или **Query Editor**
3. Скопируйте содержимое файла `database_schema.sql` из репозитория
4. Вставьте в редактор и выполните (кнопка Run)
5. Ждите завершения - должны создаться все таблицы

**Вариант B: Через командную строку (psql)**

```bash
# Подключитесь к БД
psql -h amvera-alex1976-cnpq-reyting-mo-rw \
     -p 5432 \
     -U reyting_user \
     -d reytingdb

# Введите пароль когда будет запрос

# Потом скопируйте содержимое database_schema.sql и вставьте
```

Если успешно - увидите сообщения о создании таблиц.

- [ ] Таблицы созданы (можно проверить: `\dt` в psql)
- [ ] Справочные данные загружены (проверить: `SELECT COUNT(*) FROM dim_mo;`)

---

### ЭТАП 2: Развёртывание Backend (15-20 минут)

#### Шаг 2.1: Откройте консоль Amvera и создайте контейнер

1. Откройте https://console.amvera.ru
2. Нажмите **Create Application** или **New Container**
3. Выберите **Docker** как способ развёртывания

#### Шаг 2.2: Заполните BUILD конфигурацию

На экране консоли вы увидите форму. Заполните её так:

```
┌─────────────────────────────────────────┐
│ BUILD (Сборка образа)                   │
├─────────────────────────────────────────┤
│ dockerfile:                             │
│ [backend/Dockerfile]  ← вводим это      │
│                                         │
│ context:                                │
│ [.]                    ← просто точка   │
│                                         │
│ args: (оставляем пусто)                 │
└─────────────────────────────────────────┘
```

- [ ] dockerfile: `backend/Dockerfile`
- [ ] context: `.`
- [ ] args: пусто

#### Шаг 2.3: Заполните RUN конфигурацию

```
┌─────────────────────────────────────────┐
│ RUN (Запуск контейнера)                 │
├─────────────────────────────────────────┤
│ image:                                  │
│ [${BUILD_IMAGE}]       ← это как есть   │
│                                         │
│ command: skip                           │
│ (пропускаем - CMD уже в Dockerfile)     │
│                                         │
│ containerPort:                          │
│ [8000]                 ← FastAPI порт   │
│                                         │
│ persistenceMount:                       │
│ [/app/uploads] (10Gi)  ← для файлов    │
│                                         │
│ memory: [512Mi]        ← для FastAPI    │
│ cpu: [0.5]                              │
└─────────────────────────────────────────┘
```

- [ ] image: `${BUILD_IMAGE}`
- [ ] command: `skip`
- [ ] containerPort: `8000`
- [ ] persistenceMount: `/app/uploads` (размер 10Gi)
- [ ] memory: `512Mi`
- [ ] cpu: `0.5`

#### Шаг 2.4: Добавьте переменные окружения (очень важно!)

В том же окне найдите раздел **Environment Variables** или **Env**:

```
┌─────────────────────────────────────────┐
│ ENVIRONMENT VARIABLES                   │
├─────────────────────────────────────────┤
│ DATABASE_URL =                          │
│ postgresql://reyting_user:ПАРОЛЬ@      │
│ amvera-alex1976-cnpq-reyting-mo-rw:    │
│ 5432/reytingdb                          │
│                                         │
│ DEBUG = False                           │
│ API_TITLE = Dashboard API               │
│ API_VERSION = 1.0.0                     │
│ PYTHONUNBUFFERED = 1                    │
└─────────────────────────────────────────┘
```

Замените `ПАРОЛЬ` на реальный пароль от `reyting_user`!

- [ ] DATABASE_URL установлена правильно (с реальным паролем)
- [ ] DEBUG = False
- [ ] PYTHONUNBUFFERED = 1

#### Шаг 2.5: Установите домен

Найдите раздел **Domains**:

```
┌─────────────────────────────────────────┐
│ DOMAINS                                 │
├─────────────────────────────────────────┤
│ [✓] api.reyting.amvera.ru               │
└─────────────────────────────────────────┘
```

- [ ] Домен установлен: `api.reyting.amvera.ru`

#### Шаг 2.6: Установите маршрутизацию

Найдите раздел **Routing**:

```
┌─────────────────────────────────────────┐
│ ROUTING                                 │
├─────────────────────────────────────────┤
│ Path: /api                              │
│ Port: 8000                              │
│ Rewrite: (пусто)                        │
│                                         │
│ Path: /docs                             │
│ Port: 8000                              │
│ Rewrite: (пусто)                        │
└─────────────────────────────────────────┘
```

- [ ] `/api` → Port 8000
- [ ] `/docs` → Port 8000 (для документации API)

#### Шаг 2.7: Нажмите Deploy

Кнопка обычно внизу экрана.

```
[Deploy] ← НАЖИМАЕМ ЗДЕСЬ
```

- [ ] Статус изменился на "Deploying..." или "Building..."
- [ ] Ждите 2-3 минуты (контейнер собирается)
- [ ] Статус должен стать "Running" (зелёный)

#### Шаг 2.8: Проверьте что Backend работает

После успешного развёртывания:

1. Откройте в браузере: https://api.reyting.amvera.ru/health
   - Должен вернуть: `{"status": "ok"}`

2. Откройте документацию API: https://api.reyting.amvera.ru/docs
   - Должны видеть интерактивную документацию (Swagger UI)

- [ ] Health check возвращает 200 OK
- [ ] API документация доступна

---

### ЭТАП 3: Развёртывание Frontend (15-20 минут)

#### Шаг 3.1: Создайте новый контейнер для Frontend

Повторите процесс из ЭТАПА 2, но с другими параметрами.

#### Шаг 3.2: Заполните BUILD конфигурацию

```
┌─────────────────────────────────────────┐
│ BUILD (Сборка образа)                   │
├─────────────────────────────────────────┤
│ dockerfile:                             │
│ [frontend/Dockerfile]  ← вводим это     │
│                                         │
│ context:                                │
│ [.]                    ← просто точка   │
└─────────────────────────────────────────┘
```

- [ ] dockerfile: `frontend/Dockerfile`
- [ ] context: `.`

#### Шаг 3.3: Заполните RUN конфигурацию

```
┌─────────────────────────────────────────┐
│ RUN (Запуск контейнера)                 │
├─────────────────────────────────────────┤
│ image:                                  │
│ [${BUILD_IMAGE}]       ← это как есть   │
│                                         │
│ command: skip                           │
│                                         │
│ containerPort:                          │
│ [80]                   ← для Nginx      │
│                                         │
│ persistenceMount: (оставляем пусто)     │
│                                         │
│ memory: [256Mi]        ← для React      │
│ cpu: [0.25]                             │
└─────────────────────────────────────────┘
```

- [ ] image: `${BUILD_IMAGE}`
- [ ] command: `skip`
- [ ] containerPort: `80`
- [ ] persistenceMount: пусто
- [ ] memory: `256Mi`
- [ ] cpu: `0.25`

#### Шаг 3.4: Добавьте переменные окружения

```
┌─────────────────────────────────────────┐
│ ENVIRONMENT VARIABLES                   │
├─────────────────────────────────────────┤
│ REACT_APP_API_URL =                     │
│ https://api.reyting.amvera.ru/api       │
│                                         │
│ NODE_ENV = production                   │
└─────────────────────────────────────────┘
```

- [ ] REACT_APP_API_URL = `https://api.reyting.amvera.ru/api`
- [ ] NODE_ENV = `production`

#### Шаг 3.5: Установите домен

```
┌─────────────────────────────────────────┐
│ DOMAINS                                 │
├─────────────────────────────────────────┤
│ [✓] reyting.amvera.ru                   │
│ [✓] www.reyting.amvera.ru (опционально) │
└─────────────────────────────────────────┘
```

- [ ] Домен установлен: `reyting.amvera.ru`

#### Шаг 3.6: Установите маршрутизацию

```
┌─────────────────────────────────────────┐
│ ROUTING                                 │
├─────────────────────────────────────────┤
│ Path: /                                 │
│ Port: 80                                │
│ Rewrite: /                              │
└─────────────────────────────────────────┘
```

- [ ] `/` → Port 80, Rewrite `/`

#### Шаг 3.7: Нажмите Deploy

- [ ] Статус: Deploying → Building → Running

#### Шаг 3.8: Проверьте что Frontend работает

1. Откройте в браузере: https://reyting.amvera.ru
   - Должна загрузиться главная страница приложения

2. Проверьте что приложение подключается к API:
   - Откройте вкладку **Network** в DevTools браузера (F12)
   - Перейдите на страницу рейтинга
   - Должны видеть API запросы к `https://api.reyting.amvera.ru/api`
   - Запросы должны вернуть статус 200

- [ ] Frontend загружается без ошибок
- [ ] Данные рейтинга видны в таблице
- [ ] API запросы успешны (статус 200)

---

## 🎉 ВСЁ ГОТОВО!

Если все пункты выше отмечены ✓, то приложение полностью развёрнуто на Amvera и работает!

### Ваше приложение доступно:

```
Frontend (Интерфейс):  https://reyting.amvera.ru
API Documentation:     https://api.reyting.amvera.ru/docs
API Health Check:      https://api.reyting.amvera.ru/health
```

---

## 🆘 ЕСЛИ ЧТО-ТО ПОШЛО НЕ ТАК

### Backend не запускается:

1. Откройте контейнер Backend в консоли Amvera
2. Нажмите на **Logs** (логи)
3. Ищите красные сообщения об ошибках

**Частые ошибки:**

```
ERROR: can't connect to database
  ↓ Решение: Проверьте DATABASE_URL и пароль

ERROR: module not found
  ↓ Решение: Убедитесь что context = .

ERROR: Dockerfile not found
  ↓ Решение: Проверьте что путь = backend/Dockerfile
```

### Frontend не загружается:

1. Откройте браузер (F12) → Console
2. Ищите ошибки в консоли
3. Проверьте Network вкладку на ошибки при загрузке статических файлов

**Частые ошибки:**

```
CORS error when fetching from API
  ↓ Решение: Backend должен вернуть CORS headers

API_URL is undefined
  ↓ Решение: Проверьте REACT_APP_API_URL в Environment Variables

Cannot GET /
  ↓ Решение: Проверьте containerPort = 80 и routing path = /
```

### Если нужна помощь:

1. Смотрите логи контейнера в консоли Amvera
2. Читайте подробные руководства:
   - `AMVERA_CONFIGURATION_GUIDE.md` - что выбирать
   - `AMVERA_CONFIGURATION.md` - подробное объяснение параметров
   - `AMVERA_SETUP.md` - настройка БД
   - `AMVERA_DEPLOY.md` - варианты развёртывания

3. Проверьте GitHub Issues: https://github.com/Aleksey341/Reyting/issues

---

## 📞 КОНТАКТЫ

- GitHub репозиторий: https://github.com/Aleksey341/Reyting
- Amvera платформа: https://amvera.ru
- Документация Amvera: https://amvera.ru/docs

---

**Версия**: 1.0.0
**Дата создания**: 04.11.2025
**Последнее обновление**: 04.11.2025
