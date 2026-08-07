"""Serialize models to the API response format expected by the frontend/tests."""


def _format_datetime(dt):
    if dt is None:
        return None
    value = dt.isoformat()
    if value.endswith("+00:00"):
        return value.replace("+00:00", "Z")
    if not value.endswith("Z") and "+" not in value:
        return f"{value}Z"
    return value


def serialize_user(user):
    return {
        "_id": str(user.id),
        "name": user.name,
        "email": user.email,
        "avatar": user.avatar,
    }


def serialize_comment(comment):
    return {
        "_id": str(comment.id),
        "issue": str(comment.issue_id),
        "user": serialize_user(comment.user),
        "content": comment.content,
        "isEdited": comment.is_edited,
        "createdAt": _format_datetime(comment.created_at),
        "updatedAt": _format_datetime(comment.updated_at),
    }
