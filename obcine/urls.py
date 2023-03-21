from django.urls import path

from . import views

urlpatterns = [
    path('pregled/<int:municipality_id>/', views.overview, name='overview'),
    path('pregled/<int:municipality_id>/<int:year_id>/', views.overview, name='overview'),

    path('razrez-sredstev/<int:municipality_id>/', views.cut_of_funds, name='cut_of_funds'),
    path('razrez-sredstev/<int:municipality_id>/<int:year_id>/', views.cut_of_funds, name='cut_of_funds'),

    path('prikaz-sredstav-skozi-cas/<int:municipality_id>/', views.comparison_over_time, name='comparison_over_time'),
]
