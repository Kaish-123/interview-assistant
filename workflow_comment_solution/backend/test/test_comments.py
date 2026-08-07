import json

import pytest
from django.test import Client

from api.models import Activity, Comment, Issue, User


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def user(db):
    return User.objects.create(
        name="Alex Rivers",
        email="alex@workflow.dev",
        password="Password@123",
        avatar="https://avatar.url/alex",
    )


@pytest.fixture
def other_user(db):
    return User.objects.create(
        name="Other User",
        email="other@workflow.dev",
        password="Password@123",
        avatar="https://avatar.url/other",
    )


@pytest.fixture
def issue(db, user):
    return Issue.objects.create(
        title="Implement data export feature",
        description="Allow users to export their data in various formats",
        created_by=user,
    )


def auth_header(user):
    return {"HTTP_AUTHORIZATION": f"Bearer {user.id}"}


@pytest.mark.django_db
class TestCreateComment:
    def test_create_comment_success(self, client, user, issue):
        response = client.post(
            f"/api/comments/issue/{issue.id}",
            data=json.dumps({"content": "This looks good, let's proceed with this approach."}),
            content_type="application/json",
            **auth_header(user),
        )

        assert response.status_code == 201
        payload = response.json()
        assert "comment" in payload
        comment_data = payload["comment"]
        assert comment_data["content"] == "This looks good, let's proceed with this approach."
        assert comment_data["issue"] == str(issue.id)
        assert comment_data["isEdited"] is False
        assert comment_data["user"]["_id"] == str(user.id)
        assert comment_data["user"]["name"] == "Alex Rivers"
        assert comment_data["user"]["email"] == "alex@workflow.dev"
        assert "createdAt" in comment_data
        assert "updatedAt" in comment_data

        comment = Comment.objects.get(id=comment_data["_id"])
        assert comment.user_id == user.id
        assert comment.issue_id == issue.id
        assert Activity.objects.filter(
            issue=issue, user=user, action=Activity.ACTION_COMMENT_ADDED, comment=comment
        ).exists()

    def test_create_comment_missing_content(self, client, user, issue):
        response = client.post(
            f"/api/comments/issue/{issue.id}",
            data=json.dumps({}),
            content_type="application/json",
            **auth_header(user),
        )
        assert response.status_code == 400
        assert response.json() == {"message": "Content is required"}

    def test_create_comment_empty_content(self, client, user, issue):
        response = client.post(
            f"/api/comments/issue/{issue.id}",
            data=json.dumps({"content": "   "}),
            content_type="application/json",
            **auth_header(user),
        )
        assert response.status_code == 400
        assert response.json() == {"message": "Content is required"}


@pytest.mark.django_db
class TestUpdateComment:
    def test_update_comment_success(self, client, user, issue):
        comment = Comment.objects.create(
            issue=issue,
            user=user,
            content="Sample comment",
        )

        response = client.put(
            f"/api/comments/{comment.id}",
            data=json.dumps({"content": "Updated comment content with new information."}),
            content_type="application/json",
            **auth_header(user),
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["comment"]["content"] == "Updated comment content with new information."
        assert payload["comment"]["isEdited"] is True
        assert payload["comment"]["user"]["name"] == "Alex Rivers"

        comment.refresh_from_db()
        assert comment.content == "Updated comment content with new information."
        assert comment.is_edited is True

    def test_update_comment_missing_content(self, client, user, issue):
        comment = Comment.objects.create(issue=issue, user=user, content="Sample comment")
        response = client.put(
            f"/api/comments/{comment.id}",
            data=json.dumps({}),
            content_type="application/json",
            **auth_header(user),
        )
        assert response.status_code == 400
        assert response.json() == {"message": "Content is required"}

    def test_update_comment_not_found(self, client, user):
        response = client.put(
            "/api/comments/00000000-0000-0000-0000-000000000001",
            data=json.dumps({"content": "Updated content"}),
            content_type="application/json",
            **auth_header(user),
        )
        assert response.status_code == 404
        assert response.json() == {"message": "Comment not found"}

    def test_update_comment_not_authorized(self, client, user, other_user, issue):
        comment = Comment.objects.create(issue=issue, user=user, content="Sample comment")
        response = client.put(
            f"/api/comments/{comment.id}",
            data=json.dumps({"content": "Hacked content"}),
            content_type="application/json",
            **auth_header(other_user),
        )
        assert response.status_code == 403
        assert response.json() == {"message": "Not authorized"}

        comment.refresh_from_db()
        assert comment.content == "Sample comment"
        assert comment.is_edited is False
