import os
from app.config import get_settings
from app.services.calendar import CalendarService

settings = get_settings()
print("Проверка конфигурации:")
print(f"GOOGLE_CALENDAR_ID: {'✅ Установлен' if settings.google_calendar_id else '❌ Не установлен'}")
print(f"GOOGLE_SERVICE_ACCOUNT_JSON: {'✅ Установлен' if settings.google_service_account_json else '❌ Не установлен'}")
print(f"RUBITIME_API_KEY: {'✅ Установлен' if settings.rubitime_api_key else '❌ Не установлен'}")
print(f"RUBITIME_BRANCH_ID: {settings.rubitime_branch_id}")
print(f"RUBITIME_COOPERATOR_ID: {settings.rubitime_cooperator_id}")
print(f"RUBITIME_SERVICE_ID: {settings.rubitime_service_id}")

# Попытка создать календарь
try:
    calendar = CalendarService(settings)
    print("\n✅ CalendarService инициализирован успешно")
except Exception as e:
    print(f"\n❌ Ошибка инициализации CalendarService: {e}")
    import traceback
    traceback.print_exc()
