from datetime import datetime

# Тестируем парсинг даты из вашего запроса
value = "2026-07-12 15:00:00"
print(f"Исходная строка: {value}")

normalized = value.replace("Z", "+00:00").replace(" ", "T")
print(f"Нормализованная строка: {normalized}")

try:
    dt = datetime.fromisoformat(normalized)
    print(f"fromisoformat успешно: {dt}")
except ValueError as e:
    print(f"fromisoformat failed: {e}")
    dt = datetime.strptime(value.strip(), "%Y-%m-%d %H:%M:%S")
    print(f"strptime успешно: {dt}")

if dt.tzinfo is None:
    from zoneinfo import ZoneInfo
    dt = dt.replace(tzinfo=ZoneInfo("Europe/Moscow"))
    print(f"Добавлен часовой пояс: {dt}")

print(f"Итоговый результат: {dt.isoformat()}")
