from django.urls import path
from django.views.generic import RedirectView

from . import views

urlpatterns = [
    # Landing
    path("", views.landing, name="landing"),
    # Redirects for old URLs
    path(
        "pregled/<int:municipality_id>/",
        views.OldUrlRedirectView.as_view(pattern_name="overview"),
    ),
    path(
        "pregled/<int:municipality_id>/<int:year_id>/",
        views.OldUrlRedirectView.as_view(pattern_name="overview"),
    ),
    path(
        "razrez-sredstev/<int:municipality_id>/",
        views.OldUrlRedirectView.as_view(pattern_name="cut_of_funds"),
    ),
    path(
        "razrez-sredstev/<int:municipality_id>/<int:year_id>/",
        views.OldUrlRedirectView.as_view(pattern_name="cut_of_funds"),
    ),
    path(
        "razrez-sredstev/<int:municipality_id>/<int:year_id>/table/",
        views.OldUrlRedirectView.as_view(pattern_name="cut_of_funds_table"),
    ),
    # Pages
    path("<str:municipality_slug>/", RedirectView.as_view(pattern_name="overview")),
    path("<str:municipality_slug>/pregled/", views.overview, name="overview"),
    path(
        "<str:municipality_slug>/pregled/<str:year_slug>/",
        views.overview,
        name="overview",
    ),
    path(
        "<str:municipality_slug>/razrez-sredstev/",
        views.cut_of_funds,
        name="cut_of_funds",
    ),
    path(
        "<str:municipality_slug>/razrez-sredstev/<str:year_slug>/",
        views.cut_of_funds,
        name="cut_of_funds",
    ),
    path(
        "<str:municipality_slug>/razrez-sredstev/<str:year_slug>/table/",
        views.cut_of_funds_table,
        name="cut_of_funds_table",
    ),
]
