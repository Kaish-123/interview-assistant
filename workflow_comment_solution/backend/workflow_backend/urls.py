from django.urls import include, path

urlpatterns = [
    path("api/comments/", include("api.urls.comments")),
]
