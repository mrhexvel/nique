from core.context.event_context import EventContext
from core.routers.router import Router

router = Router()

COMMANDS = {
    "Общие": [
        "/help — показать список команд",
        "/joke — случайная шутка",
        "/me — информация о вас",
    ],
    "Админские": [
        "/ban <id> — забанить пользователя",
        "/unban <id> — разбанить пользователя",
        "/shutdown — выключить бота",
    ],
}


@router.on_message(text="/help")
async def show_help(ctx: EventContext):
    msg = "📖 Доступные команды:\n\n"
    for category, cmds in COMMANDS.items():
        msg += f"🔹 {category}:\n"
        msg += "\n".join(f"  {cmd}" for cmd in cmds) + "\n\n"

    await ctx.reply(msg)
