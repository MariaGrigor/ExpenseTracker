import json
from pathlib import Path
import os
import requests
from getpass import getpass
from dotenv import load_dotenv

# Загружаем настройки из .env
load_dotenv()

API_KEY = os.getenv("FIREBASE_API_KEY")
DATABASE_URL = os.getenv("FIREBASE_DATABASE_URL", "").rstrip("/")


def connect_firebase():
    """Авторизация и проверка доступа к Firebase"""

    if not API_KEY or not DATABASE_URL:
        print("Ошибка: проверь настройки .env")
        return

    email = input("Email пользователя Firebase: ")
    password = getpass("Пароль Firebase: ")

    # Авторизация пользователя
    url = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"

    try:
        response = requests.post(
            url,
            params={"key": API_KEY},
            json={
                "email": email,
                "password": password,
                "returnSecureToken": True
            },
            timeout=15
        )


        if response.status_code != 200:
            error = response.json().get("error", {})
            print("Ошибка авторизации:", error.get("message", "Неизвестная ошибка"))
            return


        user = response.json()
        token = user["idToken"]
        uid = user["localId"]

        print("Авторизация успешна!")

        # Проверяем доступ к облачной базе
        response = requests.get(
            f"{DATABASE_URL}/users/{uid}/operations.json",
            params={"auth": token},
            timeout=15
        )

        if response.status_code == 200:
            print("Подключение к базе успешно!")
            if response.json() is None:
                print("Облачная база пока пуста.")

                # Читаем локальные операции
            file_path = Path(__file__).with_name("expenses.json")

            with open(file_path, "r", encoding="utf-8") as file:
                operations = json.load(file)

            if not operations:
                print("Нет операций для отправки")
                return

            # Заменяем запрещённые точки в ключах
            cloud_operations = {
                key.replace(".", "~"): value
                for key, value in operations.items()
            }

            # Отправляем операции в Firebase
            upload = requests.patch(
                f"{DATABASE_URL}/users/{uid}/operations.json",
                params={"auth": token},
                json=cloud_operations,
                timeout=15
            )

            if upload.status_code == 200:
                print(f"Отправлено операций: {len(operations)}")

                # Загружаем операции из облака
                download = requests.get(
                    f"{DATABASE_URL}/users/{uid}/operations.json",
                    params={"auth": token},
                    timeout=15
                )

                if download.status_code == 200:
                    cloud_data = download.json() or {}

                    # Восстанавливаем точки в идентификаторах
                    restored = {
                        key.replace("~", "."): value
                        for key, value in cloud_data.items()
                    }

                    print(f"Получено операций из облака: {len(restored)}")

                    # Находим записи, которых нет на компьютере
                    new_operations = {
                        key: value
                        for key, value in restored.items()
                        if key not in operations
                    }

                    if new_operations:
                        operations.update(new_operations)

                        with open(file_path, "w", encoding="utf-8") as file:
                            json.dump(operations, file, ensure_ascii=False, indent=2)

                        print(f"Загружено новых операций: {len(new_operations)}")
                    else:
                        print("Локальные данные уже актуальны.")

                else:
                    print("Ошибка загрузки:", download.status_code)


            else:
                print("Ошибка отправки:", upload.status_code)
                print("Ответ Firebase:", upload.text)

        else:
            print("Ошибка доступа к базе:", response.status_code)

    except requests.RequestException:
        print("Ошибка сетевого соединения с Firebase")


if __name__ == "__main__":
    connect_firebase()
