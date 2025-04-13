import time
import requests
import argparse


def login_to_django(base_url, username, password):
    """Аутентификация в Django и получение сессии"""
    session = requests.Session()

    # Сначала получаем CSRF-токен с страницы входа
    login_page_url = f"{base_url}/accounts/login/"
    response = session.get(login_page_url)

    # Получаем CSRF-токен из куки или из страницы
    csrf_token = session.cookies.get('csrftoken')

    if not csrf_token:
        # Если токен не найден в куках, пытаемся извлечь из HTML
        import re
        csrf_match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', response.text)
        if csrf_match:
            csrf_token = csrf_match.group(1)

    if not csrf_token:
        print("CSRF токен не найден. Возможно, страница входа имеет другой URL или формат.")
        return None

    # Выполняем вход
    login_data = {
        'username': username,
        'password': password,
        'csrfmiddlewaretoken': csrf_token
    }

    headers = {
        'Referer': login_page_url,
        'X-CSRFToken': csrf_token
    }

    login_response = session.post(login_page_url, data=login_data, headers=headers, allow_redirects=True)

    # Проверяем успешность входа
    if login_response.url != login_page_url and 'sessionid' in session.cookies:
        print(f"Вход выполнен успешно. Перенаправлен на: {login_response.url}")
        return session
    else:
        print("Не удалось войти. Проверьте URL входа и учетные данные.")
        return None


def measure_performance(base_url, session, endpoints, data=None):
    """Измерение производительности"""
    total_time = 0
    results = {}

    for endpoint in endpoints:
        url = f"{base_url}{endpoint}"

        # Определяем метод запроса в зависимости от эндпоинта
        if endpoint.endswith("/update/"):
            method = "POST"  # В Django формы обычно используют POST
            endpoint_data = data
        elif endpoint.endswith("/add-note/"):
            method = "POST"
            endpoint_data = data
        else:
            method = "GET"
            endpoint_data = None

        start_time = time.time()

        if method == "GET":
            response = session.get(url)
        elif method == "POST":
            # Получаем CSRF-токен перед отправкой POST
            get_response = session.get(url)
            csrf_token = session.cookies.get('csrftoken')

            headers = {
                'Referer': url,
                'X-CSRFToken': csrf_token
            }

            response = session.post(url, data=endpoint_data, headers=headers)

        end_time = time.time()
        execution_time = end_time - start_time
        total_time += execution_time

        results[endpoint] = {
            "method": method,
            "status_code": response.status_code,
            "time": execution_time,
        }

        print(f"{method} {endpoint}: {execution_time:.4f} секунд, статус: {response.status_code}")

    print(f"\nОбщее время выполнения: {total_time:.4f} секунд")
    return results, total_time


def main():
    """Основная функция запуска тестирования"""
    parser = argparse.ArgumentParser(description='Тестирование производительности Django-приложения с заметками')
    parser.add_argument('--url', default='http://localhost:8000', help='Базовый URL приложения')
    parser.add_argument('--username', default='admin', help='Имя пользователя для входа')
    parser.add_argument('--password', default='admin', help='Пароль для входа')

    args = parser.parse_args()
    base_url = args.url

    # Список эндпоинтов для тестирования
    endpoints = [
        "/notes/",
        "/notes/1/",
        "/notes/note/4/",
        "/notes/note/4/update/",
        "/notes/add-note/",
    ]

    # Данные для создания/обновления заметки
    note_data = {
        "title": "Тестовая заметка",
        "content": "Содержимое тестовой заметки",
        "category": "1",  # Django формы часто ожидают строковые значения
    }

    # Вход в систему
    session = login_to_django(base_url, args.username, args.password)

    if session:
        print("\nТестирование синхронного API...")
        measure_performance(base_url, session, endpoints, note_data)


if __name__ == "__main__":
    main()