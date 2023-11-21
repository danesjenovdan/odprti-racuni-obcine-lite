from django.urls import path
from django.views.generic import RedirectView

from . import views

urlpatterns = [
    path('', views.landing, name='landing'),

    # Redirects for old URLs
    path('prikaz-sredstav-skozi-cas/<path:path>', RedirectView.as_view(url='/prikaz-sredstev-skozi-cas/%(path)s', query_string=True)),

    path('pregled/<int:municipality_id>/', views.overview, name='overview'),
    path('pregled/<int:municipality_id>/<int:year_id>/', views.overview, name='overview'),

    path('razrez-sredstev/<int:municipality_id>/', views.cut_of_funds, name='cut_of_funds'),
    path('razrez-sredstev/<int:municipality_id>/<int:year_id>/', views.cut_of_funds, name='cut_of_funds'),
    path('razrez-sredstev/<int:municipality_id>/<int:year_id>/table/', views.cut_of_funds_table, name='cut_of_funds_table'),

    path('prikaz-sredstev-skozi-cas/<int:municipality_id>/', views.comparison_over_time, name='comparison_over_time'),
    path('prikaz-sredstev-skozi-cas/<int:municipality_id>/<int:year_id>/', views.comparison_over_time, name='comparison_over_time'),
    path('prikaz-sredstev-skozi-cas/<int:municipality_id>/<int:year_id>/table/', views.comparison_over_time_table, name='comparison_over_time_table'),
    path('prikaz-sredstev-skozi-cas/<int:municipality_id>/<int:year_id>/chart_data/', views.comparison_over_time_chart_data, name='comparison_over_time_chart_data'),
]
