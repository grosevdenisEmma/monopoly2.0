import logging
from telegram import Update, InputMediaPhoto
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackContext,
    filters,
)
from monopoly.game import Game
from monopoly.board_image import draw_board, get_board_image_bytes

# ========== CONFIG ==========
TOKEN = "8324318371:AAGTWZgvkDGQ59-1iO299FZFx6nZmbsl7Fg"  # <-- Вставь сюда свой токен!
games = {}  # chat_id -> Game

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# ========== HANDLERS ==========

async def start(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if chat_id not in games:
        games[chat_id] = Game(chat_id)
    await update.message.reply_text(
        "Монополия!\n\nДобавь игроков командой /join, затем /begin чтобы начать игру."
    )

async def join(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user = update.effective_user
    profile_photos = await user.get_profile_photos()
    if profile_photos.total_count > 0:
        file = await context.bot.get_file(profile_photos.photos[0][0].file_id)
        avatar_url = file.file_path
    else:
        avatar_url = ""
    if chat_id not in games:
        games[chat_id] = Game(chat_id)
    game = games[chat_id]
    ok = game.add_player(user.id, user.username or user.full_name, avatar_url)
    if ok:
        await update.message.reply_text(f"@{user.username or user.full_name} добавлен!")
    else:
        await update.message.reply_text("Нельзя присоединиться дважды или после старта.")

async def begin(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if chat_id not in games:
        await update.message.reply_text("Сначала /start!")
        return
    game = games[chat_id]
    ok = game.start()
    if ok:
        await update.message.reply_text("Игра началась!\n\nПервый ход: /roll")
        await send_board(update, context)
    else:
        await update.message.reply_text("Недостаточно игроков.")

async def roll(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user = update.effective_user
    if chat_id not in games:
        await update.message.reply_text("Сначала /start!")
        return
    game = games[chat_id]
    cp = game.get_current_player()
    if not cp or cp.user_id != user.id:
        await update.message.reply_text("Сейчас не ваш ход!")
        return
    dice = game.roll_dice()
    ok, msg = game.process_turn(user.id, dice)
    await update.message.reply_text(f"Вы выбросили: {dice[0]} и {dice[1]}\n{msg}")
    await send_board(update, context)
    if ok:
        game.next_turn()
        np = game.get_current_player()
        await update.message.reply_text(f"Следующий ход: @{np.username}\nИспользуйте /roll")

async def buy(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user = update.effective_user
    if chat_id not in games:
        await update.message.reply_text("Сначала /start!")
        return
    game = games[chat_id]
    cp = game.get_current_player()
    if not cp or cp.user_id != user.id:
        await update.message.reply_text("Сейчас не ваш ход!")
        return
    ok, msg = game.buy_property(user.id)
    await update.message.reply_text(msg)
    await send_board(update, context)

async def status(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if chat_id not in games:
        await update.message.reply_text("Нет активной игры.")
        return
    game = games[chat_id]
    await update.message.reply_text(game.get_status())

async def send_board(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    game = games[chat_id]
    img = draw_board(game)
    bio = get_board_image_bytes(img)
    await context.bot.send_photo(chat_id=chat_id, photo=bio)

async def help_command(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "/start — создать игру\n"
        "/join — присоединиться\n"
        "/begin — начать\n"
        "/roll — бросить кости\n"
        "/buy — купить клетку (если возможно)\n"
        "/status — список игроков и балансы\n"
    )

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("join", join))
    app.add_handler(CommandHandler("begin", begin))
    app.add_handler(CommandHandler("roll", roll))
    app.add_handler(CommandHandler("buy", buy))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, help_command))
    print("Бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()