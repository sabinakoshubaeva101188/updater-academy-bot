import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import requests


TOKEN = os.getenv("BOT_TOKEN")
API_URL = f"https://api.telegram.org/bot{TOKEN}"


def send_message(chat_id, text, keyboard=None):
    data = {
        "chat_id": chat_id,
        "text": text,
    }

    if keyboard:
        data["reply_markup"] = keyboard

    requests.post(f"{API_URL}/sendMessage", json=data, timeout=30)


def get_updates(offset=None):
    params = {
        "timeout": 30,
    }

    if offset is not None:
        params["offset"] = offset

    response = requests.get(
        f"{API_URL}/getUpdates",
        params=params,
        timeout=35
    )

    return response.json()


def bot_loop():
    offset = None

    while True:
        try:
            result = get_updates(offset)

            if not result.get("ok"):
                continue

            for update in result.get("result", []):
                offset = update["update_id"] + 1

                message = update.get("message")

                if not message:
                    continue

                chat_id = message["chat"]["id"]
                text = message.get("text", "")

                if text == "/start":
                    keyboard = {
                        "keyboard": [
                            [{"text": "📚 Курс"}],
                            [{"text": "📖 Материалы"}, {"text": "🛠 Инструменты"}],
                            [{"text": "ℹ️ О курсе"}]
                        ],
                        "resize_keyboard": True
                    }

                    send_message(
                        chat_id,
                        "🎓 Updater Academy\n\n"
                        "Практический курс для апдейторов.\n\n"
                        "Выберите раздел ниже:",
                        keyboard
                    )

                elif text == "📚 Курс":
                    send_message(
                        chat_id,
                        "📚 Курс Updater Academy\n\n"
                        "Здесь будет программа курса и уроки."
                    )

                elif text == "📖 Материалы":
                    send_message(
                        chat_id,
                        "📖 Учебные материалы\n\n"
                        "Здесь будут инструкции, файлы и полезные материалы."
                    )

                elif text == "🛠 Инструменты":
                    send_message(
                        chat_id,
                        "🛠 Инструменты\n\n"
                        "Здесь разместим полезные инструменты для работы апдейтора."
                    )

                elif text == "ℹ️ О курсе":
                    send_message(
                        chat_id,
                        "🎓 Updater Academy\n\n"
                        "Практический курс для тех, кто хочет освоить профессию апдейтора с нуля."
                    )

                else:
                    send_message(
                        chat_id,
                        "Используйте меню бота 👇"
                    )

        except Exception as error:
            print("Ошибка:", error)


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Updater Academy Bot is running!")

    def log_message(self, format, *args):
        return


def start_server():
    port = int(os.getenv("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    server.serve_forever()


if __name__ == "__main__":
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN is not set")

    threading.Thread(target=bot_loop, daemon=True).start()
    start_server()
