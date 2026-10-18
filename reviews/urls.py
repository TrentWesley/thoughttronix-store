from django.urls import path

from . import views

app_name = "reviews"

urlpatterns = [
    path(
        "reviews/product/<int:pk>/create/",
        views.CreateReviewView.as_view(),
        name="create",
    ),
    path(
        "reviews/product/<int:pk>/more/",
        views.ShowMoreReviewsView.as_view(),
        name="more",
    ),
    path("reviews/<int:pk>/edit/", views.EditReviewView.as_view(), name="edit"),
    path("reviews/<int:pk>/update/", views.UpdateReviewView.as_view(), name="update"),
    path(
        "reviews/<int:pk>/cancel-edit/",
        views.CancelEditView.as_view(),
        name="cancel_edit",
    ),
    path(
        "reviews/<int:pk>/delete/",
        views.DeleteConfirmView.as_view(),
        name="delete_confirm",
    ),
    path(
        "reviews/<int:pk>/delete/confirm/",
        views.DeleteReviewView.as_view(),
        name="delete",
    ),
    path(
        "reviews/<int:pk>/cancel-delete/",
        views.CancelDeleteView.as_view(),
        name="cancel_delete",
    ),
]
