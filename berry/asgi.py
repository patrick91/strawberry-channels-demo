import os
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from django.urls import re_path
from strawberry.channels import GraphQLHTTPConsumer, GraphQLWSConsumer

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "berry.settings")
django_asgi_app = get_asgi_application()

# Import your Strawberry schema after creating the django ASGI application
# This ensures django.setup() has been called before any ORM models are imported
# for the schema.

from api.schema import schema

websocket_urlpatterns = [
    re_path(r"graphql", GraphQLWSConsumer.as_asgi(schema=schema)),
]


gql_http_consumer = AuthMiddlewareStack(GraphQLHTTPConsumer.as_asgi(schema=schema))
gql_ws_consumer = GraphQLWSConsumer.as_asgi(schema=schema)
application = ProtocolTypeRouter(
    {
        "http": URLRouter(
            [
                re_path("^graphql", gql_http_consumer),
                re_path(
                    "^", django_asgi_app
                ),  # This might be another endpoints in your app
            ]
        ),
        "websocket": AuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
    }
)
