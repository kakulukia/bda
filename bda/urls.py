from django.conf.urls import url, include
from django.contrib import admin
from rest_framework_extensions.routers import ExtendedDefaultRouter
from rest_framework_swagger.views import get_swagger_view

from areas.views import BioListView, AreaBioView, add_bio, AreaBioViewSet, BioEntryViewSet, get_graph, PostedGraphView, \
    publish_graph, send_graph, AreaBioEditView

# construct API URLs
router = ExtendedDefaultRouter()
router.register(r'area-bios', AreaBioViewSet, base_name='are-bios').register(
    r'entries', BioEntryViewSet, base_name='bio-entries', parents_query_lookups=['area_bio'])


schema_view = get_swagger_view(title='AREA BIO API')

urlpatterns = [

    # ADMIN
    url(r'^admin/', admin.site.urls),
    url(r'^admin/translate/', include('rosetta.urls')),

    # REST API
    url(r'^api/', include(router.urls)),
    url(r'^api/docs/', schema_view),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),

    # VIEWS
    url(r'^$', BioListView.as_view(), name='index'),
    url(r'^graph/add/', add_bio),
    url(r'^graph/done/', PostedGraphView.as_view(), name='done'),
    url(r'^graph/edit/(?P<pk>[\w-]+)/$', AreaBioEditView.as_view(), name='edit-graph'),
    url(r'^graph/(?P<pk>[\w-]+)/publish/$', publish_graph, name='publish-graph'),
    url(r'^graph/(?P<pk>[\w-]+)/send/$', send_graph, name='send-graph'),

    url(r'^view-graph/(?P<uuid>[\w-]+)/$', AreaBioView.as_view(), name='view-graph'),

    url(r'^graph/(?P<pk>[\w-]+)/$', get_graph, {'stretched': False}, name='show-graph'),
    url(r'^graph/(?P<pk>[\w-]+)/bare/$', get_graph, {'bare': True}, name='show-bare-graph'),
    url(r'^graph/(?P<pk>[\w-]+)/bare-name/$', get_graph, {'list_display': True}, name='show-bare-name-graph'),
    url(r'^graph/(?P<pk>[\w-]+)/bare/original/$', get_graph, {'bare': True, 'original': True}, name='show-bare-graph'),
]

