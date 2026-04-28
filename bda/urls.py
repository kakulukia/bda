from django.urls import include, path, re_path
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView
from rest_framework import routers

from areas.views import BioListView, AreaBioView, AreaBioViewSet, get_graph, AreaBioSiteView, export_graph_svg

# construct API URLs
router = routers.DefaultRouter()
router.register(r'area-bios', AreaBioViewSet, basename='area-bios')


urlpatterns = [

    # ADMIN
    re_path(r'^admin/', admin.site.urls),
    path('favicon.ico', RedirectView.as_view(url='static/favicon.ico')),
    path('login/', auth_views.LoginView.as_view(template_name='login.pug'), name='login'),


    # REST API
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),

    # VIEWS
    path('', BioListView.as_view(), name='index'),
    re_path(r'^graph/(?P<uuid>[\w-]+)/view/$', AreaBioSiteView.as_view(), name='view-graph-page'),
    re_path(r'^graph/(?P<uuid>[\w-]+)/export\.svg$', export_graph_svg, name='export-graph-svg'),
    re_path(r'^view-graph/(?P<uuid>[\w-]+)/$', AreaBioView.as_view(), name='view-graph'),

    re_path(r'^graph/(?P<pk>\d+)/$', get_graph, {'stretched': False}, name='show-graph'),
    re_path(r'^graph/(?P<pk>\d+)/bare/$', get_graph, {'bare': True}, name='show-bare-graph'),
    re_path(r'^graph/(?P<pk>\d+)/bare-name/$', get_graph,
        {'list_display': True, 'bare': True}, name='show-bare-name-graph'),
    re_path(r'^graph/(?P<pk>\d+)/bare/original/$', get_graph, {'bare': True, 'original': True}, name='show-bare-graph'),
]
