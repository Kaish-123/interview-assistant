from django.urls import path

from api.views import comments

urlpatterns = [
    path("issue/<uuid:issue_id>", comments.create_comment, name="create-comment"),
    path("<uuid:comment_id>", comments.update_comment, name="update-comment"),
]
