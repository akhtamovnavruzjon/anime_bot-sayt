import os
import asyncio
import logging
import django

# Django muhitini sozlash
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from asgiref.sync import sync_to_async
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot_app.models import Anime, Episode,TelegramUser

BOT_TOKEN = "8706869204:AAF-ZYMRvDaMSj_0kHxPyqtUOw2yVBJiNz8"
ADMIN_ID = 7302808868


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# Yordamchi funksiya: Muayyan fasl uchun tugmalar va matnni tayyorlash
async def build_anime_keyboard(anime_id: int, current_season: int):
    # Anime va unga tegishli barcha fasllar ro'yxatini olish
    anime = await sync_to_async(
        lambda: Anime.objects.prefetch_related('episodes').filter(id=anime_id).first()
    )()

    if not anime:
        return None, None, None

    # Barcha bor fasllarni aniqlaymiz (masalan: [1, 2, 3])
    seasons = await sync_to_async(
        lambda: list(anime.episodes.values_list('season', flat=True).distinct().order_by('season'))
    )()

    if not seasons:
        return anime, None, "🍿 **Animaga hali qismlar joylanmagan.**"

    # Agar so'ralgan fasl bazada bo'lmasa, birinchi faslni o'rnatamiz
    if current_season not in seasons:
        current_season = seasons[0]

    # Faqat tanlangan fasl epizodlarini olish
    episodes = await sync_to_async(
        lambda: list(anime.episodes.filter(season=current_season).order_by('episode_number'))
    )()

    builder = InlineKeyboardBuilder()

    # 1. Qismlar tugmalari (har qatorda 3 tadan)
    for ep in episodes:
        builder.button(
            text=f"{ep.episode_number}-qism",
            callback_data=f"ep_{ep.id}"
        )
    builder.adjust(3)

    # 2. Fasllar o'rtasida o'tish tugmalari (Navigatsiya)
    nav_buttons = []
    current_index = seasons.index(current_season)

    # Chapga (Oldingi fasl)
    if current_index > 0:
        prev_season = seasons[current_index - 1]
        nav_buttons.append(
            types.InlineKeyboardButton(
                text=f"⬅️ {prev_season}-fasl",
                callback_data=f"season_{anime.id}_{prev_season}"
            )
        )

    # O'ngga (Keyingi fasl)
    if current_index < len(seasons) - 1:
        next_season = seasons[current_index + 1]
        nav_buttons.append(
            types.InlineKeyboardButton(
                text=f"{next_season}-faslga o'tish ➡️",
                callback_data=f"season_{anime.id}_{next_season}"
            )
        )

    if nav_buttons:
        builder.row(*nav_buttons)

    # Matnni shakllantirish
    text = f"🍿 <b>{anime.title}</b>\n🔑 Kod: {anime.code}\n📌 <b>{current_season}-fasl</b>"
    if anime.description:
        text += f"\n\n{anime.description}"
    text += "\n\n👇 Ko'rmoqchi bo'lgan qismingizni tanlang:"

    return anime, builder.as_markup(), text


# 1. /start buyrug'i
@dp.message(CommandStart())
async def start_handler(message: types.Message):
    user_id = message.from_user.id
    full_name = message.from_user.full_name
    username = f"@{message.from_user.username}" if message.from_user.username else "Mavjud emas"

    # Foydalanuvchini bazadan izlaymiz, yo'q bo'lsa yangi yaratamiz
    @sync_to_async
    def get_or_create_user():
        return TelegramUser.objects.get_or_create(
            telegram_id=user_id,
            defaults={
                'full_name': full_name,
                'username': message.from_user.username
            }
        )

    user, created = await get_or_create_user()

    # Agar yangi foydalanuvchi bo'lsa (created == True), adminga xabar yuboriladi
    if created and ADMIN_ID:
        admin_text = (
            "🎉 **Yangi foydalanuvchi qo'shildi!**\n\n"
            f"👤 **Ismi:** {full_name}\n"
            f"🆔 **Username:** {username}\n"
            f"🔢 **ID:** `{user_id}`"
        )
        try:
            await bot.send_message(chat_id=ADMIN_ID, text=admin_text, parse_mode="Markdown")
        except Exception as e:
            logging.error(f"Adminga xabar yuborishda xatolik: {e}")

    await message.answer(f"👋 Xush kelibsiz {full_name}!\n\n🎬 Anime kodi yuboring:")

# 2. File ID'larni olish uchun handlerlar
@dp.message(F.video)
async def get_video_file_id(message: types.Message):
    await message.reply(f"📹 **Video File ID:**\n\n`{message.video.file_id}`", parse_mode="Markdown")


@dp.message(F.photo)
async def get_photo_file_id(message: types.Message):
    await message.reply(f"🖼 **Photo File ID:**\n\n`{message.photo[-1].file_id}`", parse_mode="Markdown")


# 3. Kod orqali animeni qidirish (Boshlanishiga 1-faslni ko'rsatadi)
@dp.message(F.text.isdigit())
async def send_anime_by_code(message: types.Message):
    anime_code = int(message.text)

    anime = await sync_to_async(lambda: Anime.objects.filter(code=anime_code).first())()
    if not anime:
        await message.answer("⚠️ Bunday kodli anime topilmadi.")
        return

    # Default 1-fasldan boshlaymiz
    anime_obj, reply_markup, text = await build_anime_keyboard(anime.id, current_season=1)

    if not reply_markup:
        await message.answer(text)
        return

    if anime_obj.image_file_id:
        await message.answer_photo(
            photo=anime_obj.image_file_id,
            caption=text,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
    else:
        await message.answer(text, reply_markup=reply_markup, parse_mode="HTML")


# 4. Fasllar o'rtasida o'tish (Callback Query)
@dp.callback_query(F.data.startswith("season_"))
async def change_season(callback: types.CallbackQuery):
    _, anime_id, target_season = callback.data.split("_")
    anime_id, target_season = int(anime_id), int(target_season)

    anime, reply_markup, text = await build_anime_keyboard(anime_id, current_season=target_season)

    # Rasm bilan yuborilgan xabarni tahrirlash (Caption)
    try:
        await callback.message.edit_caption(
            caption=text,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
    except Exception:
        # Rasm bo'lmagan xabarlar uchun
        await callback.message.edit_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )

    await callback.answer()


# 5. Qism bosilganda videoni yuborish
@dp.callback_query(F.data.startswith("ep_"))
async def send_episode_video(callback: types.CallbackQuery):
    episode_id = int(callback.data.split("_")[1])

    episode = await sync_to_async(
        lambda: Episode.objects.select_related('anime').filter(id=episode_id).first()
    )()

    if episode:
        caption_text = (
            f"🎬 <b>{episode.anime.title}</b>\n"
            f"📌 {episode.season}-fasl {episode.episode_number}-qism"
        )
        await callback.answer("Video yuklanmoqda...")
        await callback.message.answer_video(
            video=episode.file_id,
            caption=caption_text,
            parse_mode="HTML"
        )
    else:
        await callback.answer("⚠️ Video topilmadi.", show_alert=True)

# 6. Har qanday noto'g'ri matn kelganda (Eng pastda bo'lishi shart!)
@dp.message(F.text)
async def invalid_text_handler(message: types.Message):
    await message.answer("⚠️ **Iltimos, animeni faqat kodini yuboring!**", parse_mode="Markdown")

async def main():
    logging.basicConfig(level=logging.INFO)
    print("Bot muvaffaqiyatli ishga tushdi...")
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())