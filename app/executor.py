import os
import re
import requests
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def render_template(text: str, data: dict) -> str:
    """Подставляет значения из data в шаблон {{data.field}}."""
    def replace(match):
        key = match.group(1).strip()
        # key выглядит как "data.order_id"
        parts = key.split(".")
        value = data
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part, "")
            else:
                return ""
        return str(value)

    return re.sub(r"\{\{(.+?)\}\}", replace, text)

def execute_telegram(config: dict, data: dict):
    """Отправляет сообщение в Telegram."""
    message = render_template(config.get("message", ""), data)
    chat_id = config.get("chat_id") or TELEGRAM_CHAT_ID

    response = requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML"
        }
    )
    response.raise_for_status()

def execute_http(config: dict, data: dict):
    """Делает HTTP запрос на внешний URL."""
    url = render_template(config.get("url", ""), data)
    method = config.get("method", "POST").upper()
    body = config.get("body", {})

    # Подставляем шаблоны в значения body
    rendered_body = {
        k: render_template(v, data) if isinstance(v, str) else v
        for k, v in body.items()
    }

    response = requests.request(method, url, json=rendered_body)
    response.raise_for_status()

def execute_log(config: dict, data: dict):
    """Логирует данные в консоль."""
    message = render_template(config.get("message", ""), data)
    print(f"[LOG] {message}")

def execute_workflow(workflow: dict, input_data: dict):
    """Выполняет все actions workflow по порядку."""
    for action in workflow["actions"]:
        action_type = action["type"]
        config = action["config"]

        try:
            if action_type == "telegram":
                execute_telegram(config, input_data)
            elif action_type == "http":
                execute_http(config, input_data)
            elif action_type == "log":
                execute_log(config, input_data)
            else:
                print(f"Unknown action type: {action_type}")
        except Exception as e:
            print(f"Action {action_type} failed: {e}")
            raise