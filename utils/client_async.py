import asyncio
import time
import httpx
import argparse


async def login_to_django_async(base_url, username, password):
    """Асинхронная аутентификация в Django и получение сессии"""
    # Создаем клиент БЕЗ контекстного менеджера
    client = httpx.AsyncClient(follow_redirects=True)

    # Сначала получаем CSRF-токен с страницы входа
    login_page_url = f"{base_url}/accounts/login/"
    response = await client.get(login_page_url)

    # Получаем CSRF-токен из куки или из страницы
    csrf_token = response.cookies.get('csrftoken')

    if not csrf_token:
        # Если токен не найден в куках, пытаемся извлечь из HTML
        import re
        csrf_match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', response.text)
        if csrf_match:
            csrf_token = csrf_match.group(1)

    if not csrf_token:
        print("CSRF токен не найден. Возможно, страница входа имеет другой URL или формат.")
        await client.aclose()  # Закрываем клиент перед возвратом None
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

    login_response = await client.post(
        login_page_url,
        data=login_data,
        headers=headers
    )

    # Проверяем успешность входа
    if 'sessionid' in client.cookies:
        print(f"Вход выполнен успешно. Статус: {login_response.status_code}")
        return client
    else:
        print("Не удалось войти. Проверьте URL входа и учетные данные.")
        await client.aclose()  # Закрываем клиент перед возвратом None
        return None

async def get_csrf_token(client, url):
    """Получение CSRF-токена для POST запросов"""
    response = await client.get(url)
    csrf_token = client.cookies.get('csrftoken')
    if not csrf_token:
        import re
        csrf_match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', response.text)
        if csrf_match:
            csrf_token = csrf_match.group(1)
    return csrf_token

async def measure_async_performance(base_url, client, endpoints, data=None):
    """Измерение производительности асинхронных эндпоинтов (последовательно)"""
    total_time = 0
    results = {}

    for endpoint in endpoints:
        url = f"{base_url}{endpoint}"

        try:
            if endpoint.endswith("/update/"):
                method = "POST"
                endpoint_data = data
            elif endpoint.endswith("/add-note/"):
                method = "POST"
                endpoint_data = data
            else:
                method = "GET"
                endpoint_data = None

            start_time = time.time()

            if method == "GET":
                response = await client.get(url)
            elif method == "POST":
                csrf_token = await get_csrf_token(client, url)
                headers = {
                    'Referer': url,
                    'X-CSRFToken': csrf_token
                }
                response = await client.post(url, data=endpoint_data, headers=headers)

            end_time = time.time()
            execution_time = end_time - start_time
            total_time += execution_time

            results[endpoint] = {
                "method": method,
                "status_code": response.status_code,
                "time": execution_time,
            }

            print(f"{method} {endpoint}: {execution_time:.4f} секунд, статус: {response.status_code}")
        except Exception as e:
            print(f"Ошибка при запросе к {endpoint}: {e}")
            continue

    print(f"\nОбщее время выполнения (последовательно): {total_time:.4f} секунд")
    return results, total_time


async def measure_parallel_async_performance(base_url, client, endpoints, data=None):
    """Измерение производительности асинхронных эндпоинтов (параллельно)"""
    start_time = time.time()

    # Подготавливаем все запросы
    async def make_request(endpoint):
        url = f"{base_url}{endpoint}"

        # Определяем метод запроса в зависимости от эндпоинта
        if endpoint.endswith("/update/"):
            method = "POST"
            endpoint_data = data

            # Получаем CSRF-токен перед отправкой POST
            await client.get(url)
            csrf_token = client.cookies.get('csrftoken')

            headers = {
                'Referer': url,
                'X-CSRFToken': csrf_token
            }

            response = await client.post(url, data=endpoint_data, headers=headers)
        elif endpoint.endswith("/add-note/"):
            method = "POST"
            endpoint_data = data

            # Получаем CSRF-токен перед отправкой POST
            await client.get(url)
            csrf_token = client.cookies.get('csrftoken')

            headers = {
                'Referer': url,
                'X-CSRFToken': csrf_token
            }

            response = await client.post(url, data=endpoint_data, headers=headers)
        else:
            method = "GET"
            response = await client.get(url)

        return endpoint, method, response

    # Выполняем все запросы параллельно
    tasks = [make_request(endpoint) for endpoint in endpoints]
    results_data = await asyncio.gather(*tasks)

    end_time = time.time()
    total_time = end_time - start_time

    # Обработка результатов
    results = {}
    for endpoint, method, response in results_data:
        results[endpoint] = {
            "method": method,
            "status_code": response.status_code,
        }
        print(f"{method} {endpoint}: статус: {response.status_code}")

    print(f"\nОбщее время параллельного выполнения: {total_time:.4f} секунд")
    return results, total_time


async def main_async():
    parser = argparse.ArgumentParser(description="Тестирование асинхронных представлений Django")
    parser.add_argument('--url', default='http://localhost:8000', help='Базовый URL приложения')
    parser.add_argument('--username', default='admin', help='Имя пользователя для входа')
    parser.add_argument('--password', default='admin', help='Пароль для входа')

    args = parser.parse_args()
    base_url = args.url

    # Список эндпоинтов для тестирования
    endpoints = [
        "/notes/a/",
        "/notes/anote/4/",
        "/notes/anote/4/update/",
        "/notes/anote/4/delete/",
        "/notes/aadd-note/",
        "/notes/atoggle-view/",
    ]

    # Список синхронных эндпоинтов (для сравнения)
    sync_endpoints = [
        "/notes/",
        "/notes/note/4/",
        "/notes/note/4/update/",
        "/notes/note/4/delete/",
        "/notes/add-note/",
        "/notes/toggle-view/",
    ]

    # Данные для создания/обновления заметки
    note_data = {
        "title": "Тестовая заметка (асинхронно)",
        "content": "Содержимое тестовой заметки (асинхронно)",
        "category": "1",  # Django формы часто ожидают строковые значения
    }

    # Вход в систему
    client = await login_to_django_async(base_url, args.username, args.password)

    if client:
        try:
            # Тестирование синхронных эндпоинтов
            print("\nТестирование синхронного API...")
            await measure_async_performance(base_url, client, sync_endpoints, note_data)

            # Тестирование асинхронных эндпоинтов (последовательно)
            print("\nТестирование асинхронного API (последовательно)...")
            await measure_async_performance(base_url, client, endpoints, note_data)

            # Тестирование асинхронных эндпоинтов (параллельно)
            print("\nТестирование асинхронного API (параллельно)...")
            await measure_parallel_async_performance(base_url, client, endpoints, note_data)
        finally:
            # Закрываем клиент после использования
            await client.aclose()


if __name__ == "__main__":
    asyncio.run(main_async())