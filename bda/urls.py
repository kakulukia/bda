from django.conf.urls import url, include
from django.contrib import admin
from rest_framework_extensions.routers import ExtendedDefaultRouter
from rest_framework_swagger.views import get_swagger_view

from areas.views import BioListView, AreaBioView, add_bio, AreaBioViewSet, BioEntryViewSet, get_graph

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
    url(r'^graph/edit/(?P<pk>[\w-]+)/', AreaBioView.as_view(), name='detail'),
    url(r'^graph/(?P<pk>[\w-]+)/', get_graph, name='show-graph'),
]

