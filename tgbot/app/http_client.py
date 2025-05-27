from typing import Optional

import aiohttp


class HttpClient:
    def __init__(
        self,
        local_addr: Optional[tuple[str, int]] = None,
        total_timeout: float = 60.0,
        connect_timeout: float = 5.0,
    ) -> None:
        self._local_addr = local_addr
        self._session: Optional[aiohttp.ClientSession] = None
        self._running: bool = False
        self._total_timeout = total_timeout
        self._connect_timeout = connect_timeout

    @property
    def session(self) -> aiohttp.ClientSession:
        if self._session is None:
            raise Exception("session is not initialized")

        return self._session

    async def run(self) -> None:
        if self._running:
            raise Exception("HttpClient is already running.")

        self._session = aiohttp.ClientSession(
            raise_for_status=False,
        )
        self._running = True

    async def stop(self) -> None:
        if self._session is not None:
            await self._session.close()
        self._running = False
