"""
Copy this into: backend/api/views/comment_views.py

Fixes for the broken starter code:
CREATE:
  - validate empty/missing content → 400
  - associate comment with request.user (was missing)
  - associate activity with request.user (was missing)
  - return comment.to_dict() (raw model is not JSON-serializable)

UPDATE:
  - Comment.objects.get(id=comment_id) (was get(comment_id) — invalid)
  - call comment.save() after mutating fields
  - only owner may edit → 403
  - missing comment → 404
  - return comment.to_dict()
"""

import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from ..models import Activity, Comment, Issue
from ..middleware import authenticate


@csrf_exempt
@require_http_methods(["POST"])
@authenticate
def create_comment(request, issue_id):
    try:
        data = json.loads(request.body)
        content = data.get("content")

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
            action="added_comment",
        )

        return JsonResponse({"comment": comment.to_dict()}, status=201)

    except Exception as e:
        print(f"Create comment error: {e}")
        return JsonResponse({"message": "Server error"}, status=500)


@csrf_exempt
@require_http_methods(["PUT"])
@authenticate
def update_comment(request, comment_id):
    try:
        data = json.loads(request.body)
        content = data.get("content")

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
        comment.save()

        return JsonResponse({"comment": comment.to_dict()})

    except Exception as e:
        print(f"Update comment error: {e}")
        return JsonResponse({"message": "Server error"}, status=500)
