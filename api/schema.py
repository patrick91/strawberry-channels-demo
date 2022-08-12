import os
import threading
from typing import AsyncGenerator

import strawberry
from strawberry.types import Info


@strawberry.input
class ChatRoom:
    room_name: str


@strawberry.type
class ChatRoomMessage:
    room_name: str
    current_user: str
    message: str


@strawberry.type
class Query:
    hello: str = strawberry.field(resolver=lambda: "Hello World!")


@strawberry.type
class Subscription:
    @strawberry.subscription
    async def join_chat_rooms(
        self,
        info: Info,
        rooms: list[ChatRoom],
        user: str,
    ) -> AsyncGenerator[ChatRoomMessage, None]:
        """Join and subscribe to message sent to the given rooms."""
        ws = info.context.ws
        channel_layer = ws.channel_layer

        room_ids = [f"chat_{room.room_name}" for room in rooms]

        for room in room_ids:
            # Join room group
            await channel_layer.group_add(room, ws.channel_name)

        for room in room_ids:
            await channel_layer.group_send(
                room,
                {
                    "type": "chat.message",
                    "room_id": room,
                    "message": f"process: {os.getpid()} thread: {threading.current_thread().name}"
                    f" -> Hello my name is {user}!",
                },
            )

        async for message in ws.channel_listen("chat.message", groups=room_ids):
            yield ChatRoomMessage(
                room_name=message["room_id"],
                message=message["message"],
                current_user=user,
            )


@strawberry.type
class Mutation:
    @strawberry.mutation
    async def send_chat_message(
        self,
        info: Info,
        room: ChatRoom,
        message: str,
    ) -> None:
        ws = info.context.ws
        channel_layer = ws.channel_layer

        await channel_layer.group_send(
            f"chat_{room.room_name}",
            {
                "type": "chat.message",
                "room_id": room.room_name,
                "message": message,
            },
        )


schema = strawberry.Schema(query=Query, mutation=Mutation, subscription=Subscription)
