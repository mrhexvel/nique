from core.context.event_context import EventContext
from core.routers.router import Router

router = Router()


@router.on_message(text="/me")
async def user_info(ctx: EventContext):
    user_id = ctx.event.from_id
    user = await ctx.client.request(
        "users.get", {"user_ids": user_id, "fields": "city,verified"}
    )

    if user:
        user = user[0]
        full_name = f"{user['first_name']} {user['last_name']}"
        city = user.get("city", {}).get("title", "Не указан")
        verified = "✅" if user.get("verified") else "❌"

        await ctx.reply(
            f"👤 {full_name}\n📍 Город: {city}\n✔️ Верифицирован: {verified}"
        )
    else:
        await ctx.answer("❗ Не удалось получить информацию о вас.")
