# 🚀 NiQue — удобный и масштабируемый фреймворк для VK API на Python

Добро пожаловать в **NiQue Framework** — современную библиотеку на Python 3.12 для построения ботов и сервисов в вк.
Разработан с упором на **типизацию**, **модульность**, **расширяемость** и **удобство использования**.

> 🔧 Использует `niquests` под капотом и поддерживает менеджер `uv`
> 🧠 Работает как с **сообществами**, так и с **пользователями**
> 👨‍🎓 Простые декораторы для регистрации команд

---

## 📦 Установка

```bash
uv pip install "git+https://github.com/mrhexvel/nique"
```

---

## ⚙️ Возможности

- ✅ Поддержка событий от **сообществ** и **пользователей**
- ✅ Удобная система **декораторов и хендлеров**
- ✅ Гибкие **middleware** (валидация, логирование, throttle и др.)
- ✅ Полная **типизация всех ивентов**
- ✅ Асинхронная архитектура (`async`/`await`)
- ✅ Чистый и масштабируемый **дизайн ядра**
- ✅ Использует `niquests` — быстрый, современный HTTP-клиент

---

## 🚀 Быстрый старт

```python
from vkapi.decorators import on_new_message
from vkapi.models import Message

@on_new_message() # скорее всего я поменяю логику обработки ивентов, но пока идея такая
async def handle_message(event: Message):
    if event.text == "привет":
        await event.answer("Привет 👋")
```

### 🔥 Пример запуска

```python
from vkapi.runtime import run_polling
from vkapi.config import settings

run_polling(token=settings.GROUP_TOKEN, group=True)
```

---

## 🧱 Архитектура

```
nique/
├── core/         # Диспетчеризация, маршрутизация, middleware
├── clients/      # API-клиенты для пользователей и групп
├── decorators/   # Умные декораторы для событий
├── models/       # Полная типизация событий
├── http/         # HTTP-обертка на niquests
├── config/       # Настройки запуска
├── runtime/      # Точка входа
└── examples/     # Примеры использования
```

---

## ✍️ Регистрация команд

```python
@router.on_new_message()
async def hello(event: Message):
    if event.text == "ping":
        await event.answer("pong 🏓")
```

---

## 🧩 Middleware

Добавляй промежуточную логику прямо в декораторы:

```python
@router.on_new_message([log_event, check_auth]) # тут тоже хз, скорее всего позже сделаю через классы
async def secured_handler(event: Message): ...
```

---

## 📚 Документация

📖 Полная документация доступна в `docs/` (в разработке)
Или запусти `mkdocs serve` для локального просмотра.

---

## 🤝 Контрибьютинг

Будем рады твоему участию в развитии проекта!
Смотри [CONTRIBUTING.md](CONTRIBUTING.md) для начала.

---

## 🛡️ Лицензия

Проект распространяется под лицензией **MIT**.

---

**Сделано с любовью к чистому коду, Python и VK ❤️**
