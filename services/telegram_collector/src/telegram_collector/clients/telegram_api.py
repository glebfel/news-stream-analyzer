from collections.abc import Callable, Coroutine
from datetime import datetime
from typing import Any

from news_common.models import RawPost, Source


class TelegramApiClient:
    def __init__(self, api_id: int, api_hash: str, session_name: str) -> None:
        self._api_id = api_id
        self._api_hash = api_hash
        self._session_name = session_name
        self._client: Any = None

    async def start(self, channels: list[str], on_message: Callable[[RawPost], Coroutine]) -> None:
        from telethon import TelegramClient, events

        self._client = TelegramClient(self._session_name, self._api_id, self._api_hash)
        await self._client.start()

        @self._client.on(events.NewMessage(chats=channels))
        async def handler(event: Any) -> None:
            msg = event.message
            if not msg.message:
                return
            post = RawPost(
                id=f"tg_{event.chat.username}_{msg.id}",
                source=Source.TELEGRAM,
                channel=event.chat.username,
                text=msg.message,
                url=f"https://t.me/{event.chat.username}/{msg.id}",
                posted_at=msg.date or datetime.utcnow(),
                reposts=getattr(msg, "forwards", 0) or 0,
                views=getattr(msg, "views", 0) or 0,
            )
            await on_message(post)

        await self._client.run_until_disconnected()
