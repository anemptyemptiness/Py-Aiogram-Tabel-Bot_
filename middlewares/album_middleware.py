import asyncio
from typing import Callable, Any, Awaitable, Dict

from aiogram import BaseMiddleware, F
from aiogram.types import Message, TelegramObject

from cachetools import TTLCache


class AlbumsMiddleware(BaseMiddleware):
    def __init__(self, wait_time_seconds: int):
        super().__init__()
        self.wait_time_seconds = wait_time_seconds
        self.albums_cache = TTLCache(
            ttl=float(wait_time_seconds) + 20.0,
            maxsize=1000
        )
        self.lock = asyncio.Lock()

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any],
    ) -> Any:
        if not isinstance(event, Message):
            print("%s used not for Message, but for %s", self.__class__.__name__, type(event))
            return await handler(event, data)

        event: Message

        # If there is no media_group
        # just pass update further
        if event.media_group_id is None:
            return await handler(event, data)

        album_id: str = event.media_group_id

        async with self.lock:
            self.albums_cache.setdefault(album_id, list())
            self.albums_cache[album_id].append(event)

        # Wait for some time until other updates are collected
        await asyncio.sleep(self.wait_time_seconds)

        # Find the smallest message_id in batch, this will be our only update
        # which will pass to handlers
        my_message_id = smallest_message_id = event.message_id

        item: Message
        for item in self.albums_cache[album_id]:
            smallest_message_id = min(smallest_message_id, item.message_id)

        # If current message_id in not the smallest, drop the update;
        # it's already saved in self.albums_cache
        if my_message_id != smallest_message_id:
            return

        # Если сотрудник прислал более одного фото, то скипаем апдейт
        if str(await data["state"].get_state()).split(":")[-1] == "my_photo":
            await event.answer(text="Нужно прислать одно фото!")
            return

        # Если сотрудник прислал более одного видео, то скипаем апдейт
        if str(await data["state"].get_state()).split(":")[-1] == "my_video":
            await event.answer(text="Нужно прислать видео одним файлом!")
            return

        context: F = data["state"]
        context.album = self.albums_cache[album_id]

        # Если сейчас бот в стадии заполнения дефектов паровоза, то скипаем апдейт
        if str(await data["state"].get_state()).split(":")[-1] == "photo_of_defects" or \
                str(await data["state"].get_state()).split(":")[-1] == "necessary_photos":
            for info in context.album:
                if info.video:
                    await event.answer(text="Нужны только фото!")
                    return

            await data["state"].update_data(train_has_defects=[photo.photo[-1].file_id for photo in context.album])

        if str(await data["state"].get_state()).split(":")[-1] == "photo_of_check":
            for info in context.album:
                if info.video:
                    await event.answer(text="Нужны только фото!")
                    return

            await data["state"].update_data(photo_of_check=[photo.photo[-1].file_id for photo in context.album])

        if str(await data["state"].get_state()).split(":")[-1] == "photo_of_beneficiaries":
            await data["state"].update_data(photo_of_beneficiaries=[photo.photo[-1].file_id for photo in context.album])

        if str(await data["state"].get_state()).split(":")[-1] == "necessary_photos":
            await data["state"].update_data(necessary_photos=[photo.photo[-1].file_id for photo in context.album])

        if str(await data["state"].get_state()).split(":")[-1] == "charge_video":
            await data["state"].update_data(charge_video=[video.video.file_id for video in context.album])

        return await handler(event, data)
