from django.urls import include, path, re_path
from django.contrib import admin
from django.views.generic import RedirectView
from rest_framework_nested import routers

from areas.views import BioListView, AreaBioView, add_bio, AreaBioViewSet, BioEntryViewSet, get_graph, PostedGraphView, \
    publish_graph, send_graph, AreaBioEditView

# construct API URLs
router = routers.DefaultRouter()
router.register(r'area-bios', AreaBioViewSet, basename='area-bios')

entries_router = routers.NestedDefaultRouter(router, r'area-bios', lookup='area_bio')
entries_router.register(r'entries', BioEntryViewSet, basename='area-bio-entries')


urlpatterns = [

    # ADMIN
    re_path(r'^admin/', admin.site.urls),
    path('favicon.ico', RedirectView.as_view(url='static/favicon.ico')),


    # REST API
    path('api/', include(router.urls)),
    path('api/', include(entries_router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),

    # VIEWS
    path('', BioListView.as_view(), name='index'),
    re_path(r'^graph/add/', add_bio),
    re_path(r'^graph/done/', PostedGraphView.as_view(), name='done'),
    re_path(r'^graph/edit/(?P<uuid>[\w-]+)/$', AreaBioEditView.as_view(), name='edit-graph'),
    re_path(r'^graph/(?P<pk>[\w-]+)/publish/$', publish_graph, name='publish-graph'),
    re_path(r'^graph/(?P<pk>[\w-]+)/send/$', send_graph, name='send-graph'),

    re_path(r'^view-graph/(?P<uuid>[\w-]+)/$', AreaBioView.as_view(), name='view-graph'),

    re_path(r'^graph/(?P<pk>[\w-]+)/$', get_graph, {'stretched': False}, name='show-graph'),
    re_path(r'^graph/(?P<pk>[\w-]+)/bare/$', get_graph, {'bare': True}, name='show-bare-graph'),
    re_path(r'^graph/(?P<pk>[\w-]+)/bare-name/$', get_graph,
        {'list_display': True, 'bare': True}, name='show-bare-name-graph'),
    re_path(r'^graph/(?P<pk>[\w-]+)/bare/original/$', get_graph, {'bare': True, 'original': True}, name='show-bare-graph'),
]
