import base64
from typing import Any

from loguru import logger

import tgbot.app.http_client


class YKassa:
    def __init__(self, access_token: str, shop_id: int) -> None:
        self.shop_id = shop_id
        self.access_token = access_token
        self.http_client = tgbot.app.http_client.HttpClient()
        self.base_url = "https://api.yookassa.ru/"

    async def _request(self, *, route: str, body: dict[str, Any]):
        credentials = f"{self.shop_id}:{self.access_token}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/json",
        }

        url = self.base_url + route

        async with self.http_client.session.post(
            url, headers=headers, json=body
        ) as response:
            if response.status == 200:
                data: Any = await response.json()
                logger.info(f"Successfully did {url}")
                return data
            else:
                logger.error(f"Error: {response.status}")
                text = await response.text()
                logger.error(text)
                return None

    async def generate_payment_link(self, ):
        route = "v3/payments/"

        body: dict[str, Any] = {}

        return await self._request(route=route, body=body)
