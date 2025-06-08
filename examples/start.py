from core.context.event_context import EventContext
from core.routers.router import Router

router = Router()


@router.on_message(text="Начать")
async def start(event: EventContext):
    hello_text = """Привет! Я бот, который может ответить на твои вопросы!
Чтобы узнать, что я умею, введи команду /help

Приятного пользования!"""

    await event.reply(hello_text)
