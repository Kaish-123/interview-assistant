import json
import uuid

from django.db import models
from django.utils import timezone


class User(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    avatar = models.URLField(blank=True, default="")

    def __str__(self):
        return self.email


class Issue(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="issues")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Comment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    content = models.TextField()
    is_edited = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Activity(models.Model):
    ACTION_CREATED = "created"
    ACTION_COMMENT_ADDED = "comment_added"
    ACTION_COMMENT_DELETED = "comment_deleted"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name="activities")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="activities")
    action = models.CharField(max_length=50)
    comment = models.ForeignKey(
        Comment, on_delete=models.SET_NULL, null=True, blank=True, related_name="activities"
    )
    created_at = models.DateTimeField(default=timezone.now)
