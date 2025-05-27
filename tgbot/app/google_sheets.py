from typing import Any

from loguru import logger

import tgbot.app.http_client


class GoogleSheets:
    def __init__(self, access_token: str) -> None:
        self.access_token = access_token
        self.http_client = tgbot.app.http_client.HttpClient()
        self.base_url = "https://sheets.googleapis.com/v4/spreadsheets/"

    async def _request(
        self, *, route: str, params: dict[str, str], body: dict[str, Any]
    ):
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

        url = f"{self.base_url}{route}"

        async with self.http_client.session.post(
            url, headers=headers, params=params, json=body
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

    async def add_row_to_sheet(self, spreadsheet_id: str, values: list[Any]):
        route = f"{spreadsheet_id}/values/Sheet1!A1:append"
        params = {"valueInputOption": "USER_ENTERED", "insertDataOption": "INSERT_ROWS"}

        body = {"values": [values]}

        return await self._request(route=route, params=params, body=body)
