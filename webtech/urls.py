from django.urls import path, include
from rest_framework import routers
from . import views, api_views


urlpatterns = [
    path('', views.index, name='index'),
    path('map', views.map, name='map'),
    path('bookmark_event/<int:event_id>', views.bookmark_event, name='bookmark_event'),
    path('add_venue_form_test', views.add_venue_form_test, name='add_venue_form_test'),
    path('add_event_form_test', views.add_event_form_test, name='add_event_form_test'),

    path('events/<int:event_id>', views.event_page, name='event_page'),
    path('venues/<int:venue_id>', views.venue_page, name='venue_page'),

    path('api/events/', api_views.event_list),
    path('api/events/<int:pk>/', api_views.event_detail),

    path('api/venues/', api_views.venue_list),
    path('api/venues/<int:pk>/', api_views.venue_detail),

    path('scrapelastfm/', views.scrapelastfm, name='scrapelastfm'),
    path('scrape/', views.scrape, name='scrape')
]
