from app.config import Settings
from app.models.webhook import WebhookPayload
from app.services.formatter import EventFormatter

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

# Валидируем payload
try:
    payload = WebhookPayload.model_validate(webhook_data)
    print("✅ WebhookPayload валиден")
    print(f"Event: {payload.event}")
    print(f"Record ID: {payload.record_id}")
    print(f"Record date: {payload.data.record}")
except Exception as e:
    print(f"❌ Ошибка валидации WebhookPayload: {e}")

# Тестируем formatter с дефолтными настройками
settings = Settings.from_environ()
formatter = EventFormatter(settings)

try:
    event_payload = formatter.build(payload.record_id, payload.data.model_dump(mode="python", exclude_none=False), payload.event)
    print("\n✅ GoogleEventPayload создан успешно")
    print(f"Summary: {event_payload.summary}")
    print(f"Description (первые 200 символов): {event_payload.description[:200]}...")
    print(f"Start: {event_payload.start}")
    print(f"End: {event_payload.end}")
    print(f"Location: {event_payload.location}")
except Exception as e:
    print(f"\n❌ Ошибка создания GoogleEventPayload: {e}")
    import traceback
    traceback.print_exc()
