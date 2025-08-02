from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO
from monopoly.board import Board

BOARD_SIZE = 1280
PLAYER_COLORS = [
    "#FF4500", "#1E90FF", "#228B22", "#FFD700", "#9400D3", "#00CED1", "#8B0000", "#FF69B4"
]

def get_avatar_image(avatar_url, size=64):
    try:
        response = requests.get(avatar_url)
        img = Image.open(BytesIO(response.content)).convert("RGBA")
        img = img.resize((size, size), Image.ANTIALIAS)
        return img
    except Exception:
        return Image.new("RGBA", (size, size), "#CCCCCC")

def draw_board(game, font_path="arial.ttf"):
    board = Board()
    img = Image.open("field.png").convert("RGBA")
    draw = ImageDraw.Draw(img)

    # 1. Собственность: владельцы, дома, отели
    for prop in game.properties:
        if prop.owner_id is not None:
            owner_idx = [p.user_id for p in game.players].index(prop.owner_id)
            cell = board.get_cell(prop.id)
            px, py = cell["x"], cell["y"]
            w, h = cell["width"], cell["height"]

            # Метка владельца
            draw.ellipse([px + w - 30, py + 10, px + w - 10, py + 30],
                         fill=PLAYER_COLORS[owner_idx % len(PLAYER_COLORS)], outline="#222222")

            # Дома/отель
            if prop.type == "street":
                if prop.hotel:
                    draw.rectangle([px + 10, py + h - 50, px + 50, py + h - 10],
                                   fill="#D2691E", outline="#222222")
                else:
                    for h_idx in range(prop.house_count):
                        draw.rectangle([px + 10 + h_idx * 22, py + h - 30,
                                        px + 30 + h_idx * 22, py + h - 10],
                                       fill="#006600", outline="#222222")

    # 2. Фишки игроков
    for idx, player in enumerate(game.players):
        cell = board.get_cell(player.position)
        px, py = cell["x"], cell["y"]
        w, h = cell["width"], cell["height"]

        avatar_img = get_avatar_image(player.avatar_url, size=56)
        cx = px + w // 2
        cy = py + h // 2
        img.paste(avatar_img, (cx - 28, cy - 28), avatar_img)
        draw.ellipse([cx - 30, cy - 30, cx + 30, cy + 30],
                     outline=PLAYER_COLORS[idx % len(PLAYER_COLORS)], width=4)

    # 3. Баланс игроков
    try:
        font = ImageFont.truetype(font_path, 24)
    except Exception:
        font = ImageFont.load_default()

    y_panel = BOARD_SIZE - 60
    for idx, player in enumerate(game.players):
        text = f"@{player.username}: {player.balance}₽"
        draw.text((20 + idx * 220, y_panel), text,
                  fill=PLAYER_COLORS[idx % len(PLAYER_COLORS)], font=font)

    # 4. Текущий игрок
    cp = game.get_current_player()
    if cp:
        draw.text((BOARD_SIZE // 2 - 160, BOARD_SIZE - 30),
                  f"Ход игрока: @{cp.username}", fill="#222222", font=font)

    return img

from io import BytesIO

def get_board_image_bytes(img):
    """Вернуть картинку в байтах для отправки через Telegram API"""
    bio = BytesIO()
    img.save(bio, format="PNG")
    bio.seek(0)
    return bio
