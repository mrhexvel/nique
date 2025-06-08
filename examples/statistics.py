from collections import defaultdict

from core.context.event_context import EventContext
from core.routers.router import Router

router = Router()
USER_ACTIVITY = defaultdict(int)


@router.on_message()
async def track(ctx):
    USER_ACTIVITY[ctx.event.from_id] += 1


@router.on_message(text="/stats")
async def stats(ctx: EventContext):
    sorted_users = sorted(USER_ACTIVITY.items(), key=lambda x: x[1], reverse=True)
    lines = [f"{uid}: {count} сообщений" for uid, count in sorted_users[:5]]
    await ctx.reply("📈 Топ-5 активных пользователей:\n" + "\n".join(lines))
