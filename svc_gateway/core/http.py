import asyncio
from typing import Any, Dict, Optional

import httpx


async def request_with_retry(
    method: str,
    url: str,
    *,
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    json: Any = None,
    files: Any = None,
    timeout: float = 5.0,
    retries: int = 2,
    retry_delay: float = 0.2,
) -> httpx.Response:
    """
    Выполняет HTTP запрос с простым механизмом retry.

    Args:
        method: HTTP метод
        url: целевой URL
        headers/params/json/files: параметры httpx.request
        timeout: таймаут одного запроса
        retries: количество повторных попыток
        retry_delay: базовая задержка между попытками

    Returns:
        httpx.Response

    Raises:
        httpx.TimeoutException | httpx.RequestError при исчерпании попыток
    """
    last_exception: Optional[Exception] = None

    for attempt in range(retries + 1):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    json=json,
                    files=files,
                )
                return response
        except (httpx.TimeoutException, httpx.RequestError) as exc:
            last_exception = exc
            if attempt == retries:
                raise
            await asyncio.sleep(retry_delay * (attempt + 1))

    if last_exception:
        raise last_exception
    raise RuntimeError("request_with_retry failed without exception")
