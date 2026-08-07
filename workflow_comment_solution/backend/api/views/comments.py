import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from api.models import Activity, Comment, Issue
from api.utils.serializers import serialize_comment


def _parse_json_body(request):
    try:
        return json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return {}


def _require_auth(request):
    user = getattr(request, "user", None)
    if user is None or not getattr(user, "is_authenticated", False):
        return JsonResponse({"message": "Not authorized"}, status=401)
    return None


@csrf_exempt
@require_http_methods(["POST"])
def create_comment(request, issue_id):
    auth_error = _require_auth(request)
    if auth_error:
        return auth_error

    body = _parse_json_body(request)
    content = body.get("content")
    if content is None or (isinstance(content, str) and not content.strip()):
        return JsonResponse({"message": "Content is required"}, status=400)

    try:
        issue = Issue.objects.get(id=issue_id)
    except Issue.DoesNotExist:
        return JsonResponse({"message": "Issue not found"}, status=404)

    comment = Comment.objects.create(
        issue=issue,
        user=request.user,
        content=content.strip() if isinstance(content, str) else content,
    )

    Activity.objects.create(
        issue=issue,
        user=request.user,
        action=Activity.ACTION_COMMENT_ADDED,
        comment=comment,
    )

    return JsonResponse({"comment": serialize_comment(comment)}, status=201)


@csrf_exempt
@require_http_methods(["PUT"])
def update_comment(request, comment_id):
    auth_error = _require_auth(request)
    if auth_error:
        return auth_error

    body = _parse_json_body(request)
    content = body.get("content")
    if content is None or (isinstance(content, str) and not content.strip()):
        return JsonResponse({"message": "Content is required"}, status=400)

    try:
        comment = Comment.objects.select_related("user", "issue").get(id=comment_id)
    except Comment.DoesNotExist:
        return JsonResponse({"message": "Comment not found"}, status=404)

    if str(comment.user_id) != str(request.user.id):
        return JsonResponse({"message": "Not authorized"}, status=403)

    comment.content = content.strip() if isinstance(content, str) else content
    comment.is_edited = True
    comment.save(update_fields=["content", "is_edited", "updated_at"])

    return JsonResponse({"comment": serialize_comment(comment)}, status=200)
