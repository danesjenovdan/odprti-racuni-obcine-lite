from django.urls import path

from . import views

urlpatterns = [
    path('razrez-sredstev/<int:municipality_id>/<int:year_id>/', views.cut_off_funds),
    path('tok-sredstev/<int:municipality_id>/<int:year_id>/', views.budet_flow),
    path('prikaz-sredstav-skozi-cas/<int:municipality_id>/<int:year_id>/', views.over_the_years),
]
