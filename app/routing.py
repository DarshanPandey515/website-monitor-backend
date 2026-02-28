from django.urls import path
from .consumers import WebsiteConsumer

websocket_urlpatterns = [
    path("ws/monitor/", WebsiteConsumer.as_asgi()),
]