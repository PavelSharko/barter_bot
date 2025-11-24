import aiohttp


async def ask_n8n_agent_unic(url1: str, url2: str, payload: dict, attempt: int = 1) -> dict:
    """
    Асинхронно отправляет запрос с данными (payload) на указанный url1.
    Если попытка неудачна, пробует резервный url2.

    Аргументы:
        url1 (str): основной адрес для отправки POST-запроса.
        url2 (str): резервный адрес для повторной попытки (если основной недоступен).
        payload (dict): данные запроса, отправляемые в теле POST в формате JSON.
        attempt (int): текущий номер попытки (по умолчанию 1, не требует ручного указания при внешнем вызове).

    Возвращает:
        dict: декодированный JSON-ответ от сервиса n8n.

    Исключения:
        RuntimeError: выбрасывается, если обе попытки (url1 и url2) завершились ошибкой.

    Такой подход гарантирует отказоустойчивую доставку данных
    при кратковременных сбоях основного адреса n8n.
    """
    url = url1 if attempt == 1 else url2

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as resp:
                resp.raise_for_status()
                return await resp.json()
    except Exception as e:
        if attempt == 1 and url2:
            # Если url2 есть, пробуем второй адрес
            return await ask_n8n_agent_unic(url1, url2, payload, attempt=2)
        else:
            # Если оба упали — пробрасываем ошибку (вызовет alert в основном методе)
            raise RuntimeError(f"❌ Ошибка при обращении к n8n ({url}): {e}") from e
