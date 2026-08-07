import json

from django.http import JsonResponse
from django.utils.functional import SimpleLazyObject

from api.models import User


def _get_user_from_token(request):
    auth_header = request.META.get("HTTP_AUTHORIZATION", "")
    if not auth_header.startswith("Bearer "):
        return None

    token = auth_header.split(" ", 1)[1].strip()
    if not token:
        return None

    try:
        return User.objects.get(id=token)
    except (User.DoesNotExist, ValueError):
        return None


class AuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = _get_user_from_token(request)
        if user is not None:
            user.is_authenticated = True
            request.user = user
        else:
            request.user = SimpleLazyObject(lambda: _AnonymousUser())
        return self.get_response(request)


class _AnonymousUser:
    is_authenticated = False
    id = None

    @staticmethod
    def get_username():
        return ""
