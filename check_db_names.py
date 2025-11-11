import requests
import json

# Получим данные с карты, чтобы увидеть названия в БД
url = "https://reyting-alex1976.amvera.io/api/map/data"

try:
    response = requests.get(url, params={"period": "2024-01"}, timeout=30)
    response.raise_for_status()
    data = response.json()
    
    print("Названия муниципалитетов в БД:")
    print("=" * 60)
    
    if data.get("data"):
        for i, mo in enumerate(data["data"], 1):
            print(f"{i:2}. {mo.get('mo_name')}")
    else:
        print("Нет данных")
        
except Exception as e:
    print(f"Ошибка: {e}")
