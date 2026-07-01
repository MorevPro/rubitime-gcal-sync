import json
import asyncio
from app.main import app
from app.config import get_settings
from fastapi.testclient import TestClient

# Создаём тестовый клиент
client = TestClient(app)

# Данные из вашего CURL-запроса
webhook_data = {
    "from": "user",
    "event": "event-create-record",
    "data": {
        "id": 8592637,
        "parent_record": None,
        "whom": 26459,
        "created_at": "2026-07-01 07:52:29",
        "updated_at": None,
        "record": "2026-07-12 15:00:00",
        "name": "ТЕСТ ИВАН",
        "price": 8000,
        "phone": "+79151807013",
        "email": "757988@mail.ru",
        "comment": "",
        "status": 0,
        "status_title": "Записан",
        "cooperator_id": 39824,
        "cooperator_title": "Задорина-Негода Галина Николаевна",
        "branch_id": 19697,
        "branch_title": "г. Москва, М. Тушинская ул. Мещерякова, 8, каб. 5",
        "service_id": 71509,
        "service_title": "Дети до 1 года (персональная тренировка)",
        "url": "https://zngn.rubitime.ru/widget/card/4a6490c1a4de980ee07a661ecfe1f30730a92a110acbed13bb9691ecd258cf61",
        "coupon": None,
        "coupon_discount": None,
        "source": None,
        "cancelReason": None,
        "duration": 60,
        "prepayment": None,
        "prepayment_date": None,
        "prepayment_url": None,
        "reminder": "2026-07-11 15:00:00",
        "custom_field1": None,
        "custom_field2": "М",
        "custom_field3": None,
        "custom_field4": None,
        "custom_field5": None,
        "custom_field6": None,
        "custom_field7": None,
        "custom_field8": None,
        "custom_field9": None,
        "custom_field10": None,
        "custom_field11": None,
        "custom_field12": None,
        "custom_field13": None,
        "custom_field14": None,
        "custom_field15": None,
        "custom_field16": None,
        "custom_field17": None,
        "custom_field18": None,
        "custom_field19": None,
        "custom_field20": None
    }
}

print("Отправка webhook-запроса...")
response = client.post(
    "/webhook",
    json=webhook_data,
    headers={"content-type": "application/json"}
)

print(f"Статус код: {response.status_code}")
print(f"Ответ: {response.json()}")

# Проверяем, что сервер запустился
print("\nПроверка health endpoint...")
health_response = client.get("/health")
print(f"Health: {health_response.json()}")
