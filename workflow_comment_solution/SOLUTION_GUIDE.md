# Workflow Comment Backend — Solution Guide

Copy into your assessment IDE. **Do not modify** `README.md`, `backend/utils/seed.py`, or `setup.sh`.

## File to update: `backend/api/views/comment_views.py`

Replace `create_comment` and `update_comment` with:

```python
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
```

Leave `delete_comment` as-is unless tests fail for delete.

## Bugs in the starter code

| Location | Bug | Fix |
|----------|-----|-----|
| `create_comment` | No content validation | Return 400 `"Content is required"` |
| `create_comment` | `Comment.objects.create(..., content=content)` missing `user` | Pass `user=request.user` |
| `create_comment` | Activity missing `user` | Pass `user=request.user` |
| `create_comment` | `JsonResponse({'comment': comment})` | Use `comment.to_dict()` |
| `update_comment` | `Comment.objects.get(comment_id)` | Use `get(id=comment_id)` |
| `update_comment` | Sets fields but never saves | Call `comment.save()` |
| `update_comment` | No owner check | Return 403 if `comment.user_id != request.user.id` |
| `update_comment` | Missing comment → 500 | Catch `DoesNotExist` → 404 |
| `update_comment` | Returns raw model | Use `comment.to_dict()` |

## Manual check

1. Login: `alex@workflow.dev` / `Password@123`
2. Open an issue → add a comment → it should appear in Activity
3. Hover your comment → edit → save → `(edited)` shows next to the timestamp

## Unit tests

```bash
cd backend
pytest
```
