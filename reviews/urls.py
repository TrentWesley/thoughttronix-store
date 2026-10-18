from django.urls import path

from . import views

app_name = "reviews"

urlpatterns = [
    path(
        "reviews/product/<int:pk>/create/",
        views.CreateReviewView.as_view(),
        name="create",
    ),
    path("reviews/<int:pk>/edit/", views.EditReviewView.as_view(), name="edit"),
    path("reviews/<int:pk>/update/", views.UpdateReviewView.as_view(), name="update"),
    path(
        "reviews/<int:pk>/cancel-edit/",
        views.CancelEditView.as_view(),
        name="cancel_edit",
    ),
]
