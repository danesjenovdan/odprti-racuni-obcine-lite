from django.urls import path
from django.views.generic import RedirectView

from . import views


urlpatterns = [
    # Landing
    path("", views.landing, name="landing"),

    # Redirects for old URLs
    path("pregled/<int:municipality_id>/", views.OldUrlRedirectView.as_view(pattern_name="overview")),
    path("pregled/<int:municipality_id>/<int:year_id>/", views.OldUrlRedirectView.as_view(pattern_name="overview")),

    path("razrez-sredstev/<int:municipality_id>/", views.OldUrlRedirectView.as_view(pattern_name="cut_of_funds")),
    path("razrez-sredstev/<int:municipality_id>/<int:year_id>/", views.OldUrlRedirectView.as_view(pattern_name="cut_of_funds")),
    path("razrez-sredstev/<int:municipality_id>/<int:year_id>/table/", views.OldUrlRedirectView.as_view(pattern_name="cut_of_funds_table")),

    path("prikaz-sredstav-skozi-cas/<path:path>", RedirectView.as_view(url="/prikaz-sredstev-skozi-cas/%(path)s", query_string=True)),
    path("prikaz-sredstev-skozi-cas/<int:municipality_id>/", views.OldUrlRedirectView.as_view(pattern_name="comparison_over_time")),
    path("prikaz-sredstev-skozi-cas/<int:municipality_id>/<int:year_id>/", views.OldUrlRedirectView.as_view(pattern_name="comparison_over_time")),
    path("prikaz-sredstev-skozi-cas/<int:municipality_id>/<int:year_id>/table/", views.OldUrlRedirectView.as_view(pattern_name="comparison_over_time_table")),
    path("prikaz-sredstev-skozi-cas/<int:municipality_id>/<int:year_id>/chart_data/", views.OldUrlRedirectView.as_view(pattern_name="comparison_over_time_chart_data")),

    # Pages
    path("<str:municipality_slug>/pregled/", views.overview, name="overview"),
    path("<str:municipality_slug>/pregled/<str:year_slug>/", views.overview, name="overview"),

    path("<str:municipality_slug>/razrez-sredstev/", views.cut_of_funds, name="cut_of_funds"),
    path("<str:municipality_slug>/razrez-sredstev/<str:year_slug>/", views.cut_of_funds, name="cut_of_funds"),
    path("<str:municipality_slug>/razrez-sredstev/<str:year_slug>/table/", views.cut_of_funds_table, name="cut_of_funds_table"),

    path("<str:municipality_slug>/prikaz-sredstev-skozi-cas/", views.comparison_over_time, name="comparison_over_time"),
    path("<str:municipality_slug>/prikaz-sredstev-skozi-cas/<str:year_slug>/", views.comparison_over_time, name="comparison_over_time"),
    path("<str:municipality_slug>/prikaz-sredstev-skozi-cas/<str:year_slug>/table/", views.comparison_over_time_table, name="comparison_over_time_table"),
    path("<str:municipality_slug>/prikaz-sredstev-skozi-cas/<str:year_slug>/chart_data/", views.comparison_over_time_chart_data, name="comparison_over_time_chart_data"),
]
