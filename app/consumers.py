import json
from channels.generic.websocket import AsyncWebsocketConsumer


class WebsiteConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        print("User in scope:", self.scope["user"])

        if user.is_anonymous:
            await self.close()
            return

        self.group_name = f"monitor_{user.id}"

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def website_updates(self, event):
        await self.send(
            text_data=json.dumps(event["data"])
        )
