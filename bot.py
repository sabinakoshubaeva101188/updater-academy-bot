import os
import time
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import requests


TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("BOT_TOKEN is not set")

API_URL = f"https://api.telegram.org/bot{TOKEN}"

ACCESS_TIME = 30 * 24 * 60 * 60
COURSE_MATERIAL_PATH = Path(__file__).parent / "course" / "UA.pptx"

users = {}


def send_message(chat_id, text, keyboard=None):
    data = {
        "chat_id": chat_id,
        "text": text,
    }

    if keyboard:
        data["reply_markup"] = keyboard

    requests.post(
        f"{API_URL}/sendMessage",
        json=data,
        timeout=30
    )


def send_course_material(chat_id):
    """Send the course presentation as a protected Telegram document."""
    with COURSE_MATERIAL_PATH.open("rb") as material:
        requests.post(
            f"{API_URL}/sendDocument",
            data={
                "chat_id": chat_id,
                "caption": "📖 Updater Academy — учебный материал курса.",
                "protect_content": "true",
            },
            files={
                "document": (
                    COURSE_MATERIAL_PATH.name,
                    material,
                    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                )
            },
            timeout=30,
        )


def get_updates(offset=None):
    params = {
        "timeout": 30,
    }

    if offset is not None:
        params["offset"] = offset

    try:
        print("CALLING TELEGRAM GETUPDATES", flush=True)

        response = requests.get(
            f"{API_URL}/getUpdates",
            params=params,
            timeout=35
        )

        print("Telegram status:", response.status_code, flush=True)
        print("Telegram response:", response.text, flush=True)

        return response.json()

    except Exception as error:
        print("GET UPDATES ERROR:", error, flush=True)
        return {"ok": False}


def has_access(chat_id):
    user = users.get(chat_id)

    if not user:
        return False

    expires_at = user.get("expires_at", 0)

    return time.time() < expires_at


def main_menu():
    return {
        "keyboard": [
            [{"text": "📚 Курс"}],
            [{"text": "📖 Материалы"}, {"text": "🛠 Инструменты"}],
            [{"text": "💳 Купить курс"}],
            [{"text": "ℹ️ О курсе"}]
        ],
        "resize_keyboard": True
    }


def course_menu():
    return {
        "keyboard": [
            [{"text": "📖 Материалы"}],
            [{"text": "📅 Мой доступ"}],
            [{"text": "⬅️ Главное меню"}]
        ],
        "resize_keyboard": True
    }


def bot_loop():
    print("BOT LOOP STARTED", flush=True)

    offset = None

    while True:
        try:
            result = get_updates(offset)

            if not result.get("ok"):
                print("Telegram API returned an error:", result, flush=True)
                time.sleep(2)
                continue

            for update in result.get("result", []):
                offset = update["update_id"] + 1

                message = update.get("message")

                if not message:
                    continue

                chat_id = message["chat"]["id"]
                text = message.get("text", "")

                if text == "/start":
                    send_message(
                        chat_id,
                        "🎓 Updater Academy\n\n"
                        "Практический курс для апдейторов.\n\n"
                        "Выберите раздел ниже:",
                        main_menu()
                    )

                elif text == "📚 Курс":
                    if has_access(chat_id):
                        send_message(
                            chat_id,
                            "🎓 Вы получили доступ к курсу.\n\n"
                            "Доступ действует 30 дней.\n\n"
                            "Выберите раздел:",
                            course_menu()
                        )
                    else:
                        send_message(
                            chat_id,
                            "🔒 Курс доступен только после покупки.\n\n"
                            "Стоимость курса: 2 990 сом.\n\n"
                            "Нажмите «💳 Купить курс».",
                            main_menu()
                        )

                elif text == "📖 Материалы":
                    if has_access(chat_id):
                        send_message(
                            chat_id,
                            "📖 Учебные материалы\n\n"
                            "Отправляю презентацию курса.\n\n"
                            "🔐 Документ защищён и доступен в течение 30 дней."
                        )
                        send_course_material(chat_id)
                    else:
                        send_message(
                            chat_id,
                            "🔒 Доступ к материалам закрыт.\n\n"
                            "Сначала необходимо приобрести курс.",
                            main_menu()
                        )

                elif text == "🛠 Инструменты":
                    if has_access(chat_id):
                        send_message(
                            chat_id,
                            "🛠 Инструменты для апдейтора\n\n"
                            "Раздел доступен участникам курса."
                        )
                    else:
                        send_message(
                            chat_id,
                            "🔒 Этот раздел доступен только участникам курса.",
                            main_menu()
                        )

                elif text == "💳 Купить курс":
                    send_message(
                        chat_id,
                        "💳 Покупка курса\n\n"
                        "🎓 Updater Academy\n"
                        "Практический курс для апдейторов.\n\n"
                        "Стоимость: 2 990 сом.\n"
                        "Срок доступа: 30 дней.\n\n"
                        "После оплаты доступ будет активирован.\n\n"
                        "⚠️ Система оплаты подключим следующим этапом."
                    )

                elif text == "📅 Мой доступ":
                    if has_access(chat_id):
                        expires_at = users[chat_id]["expires_at"]

                        remaining = int(
                            (expires_at - time.time()) / 86400
                        )

                        if remaining < 0:
                            remaining = 0

                        send_message(
                            chat_id,
                            f"🔐 Ваш доступ активен.\n\n"
                            f"Осталось примерно: {remaining} дней."
                        )
                    else:
                        send_message(
                            chat_id,
                            "🔒 Активного доступа нет.\n\n"
                            "Приобретите курс, чтобы получить доступ.",
                            main_menu()
                        )

                elif text == "ℹ️ О курсе":
                    send_message(
                        chat_id,
                        "🎓 Updater Academy\n\n"
                        "Практический курс для тех, кто хочет "
                        "освоить профессию апдейтера.\n\n"
                        "📚 Уроки\n"
                        "📖 Учебные материалы\n"
                        "🛠 Инструменты\n"
                        "🔐 Доступ на 30 дней\n\n"
                        "Стоимость: 2 990 сом.",
                        main_menu()
                    )

                elif text == "⬅️ Главное меню":
                    send_message(
                        chat_id,
                        "Главное меню 👇",
                        main_menu()
                    )

                else:
                    send_message(
                        chat_id,
                        "Используйте меню бота 👇",
                        main_menu()
                    )

        except Exception as error:
            print("Ошибка:", error, flush=True)
            time.sleep(3)


class HealthHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(
            b"Updater Academy Bot is running!"
        )

    def log_message(self, format, *args):
        return


def start_server():
    port = int(os.getenv("PORT", 10000))

    server = HTTPServer(
        ("0.0.0.0", port),
        HealthHandler
    )

    server.serve_forever()


if __name__ == "__main__":

    threading.Thread(
        target=bot_loop,
        daemon=True
    ).start()

    start_server()
