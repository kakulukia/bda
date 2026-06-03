from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.http import HttpResponseRedirect
from django.urls import include, path, re_path
from django.views.generic import RedirectView
from rest_framework import routers

from areas.views import BioListView, AreaBioViewSet, get_graph, export_graph_svg

# construct API URLs
router = routers.DefaultRouter()
router.register(r'area-bios', AreaBioViewSet, basename='area-bios')


urlpatterns = [

    # ADMIN
    path('admin/', include('loginas.urls')),
    path('admin/', admin.site.urls),
    path('favicon.ico', RedirectView.as_view(url='static/favicon.ico')),
    path('login/', auth_views.LoginView.as_view(template_name='login.pug'), name='login'),


    # REST API
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),

    # VIEWS
    path('', BioListView.as_view(), name='index'),
    path('__reload__/', include('django_browser_reload.urls')),
    re_path(r'^graph/(?P<uuid>[\w-]+)/export\.svg$', export_graph_svg, name='export-graph-svg'),

    re_path(r'^graph/(?P<pk>\d+)/$', get_graph, {'stretched': False}, name='show-graph'),
    re_path(r'^graph/(?P<pk>\d+)/bare/$', get_graph, {'bare': True}, name='show-bare-graph'),
    re_path(r'^graph/(?P<pk>\d+)/bare-name/$', get_graph,
        {'list_display': True, 'bare': True}, name='show-bare-name-graph'),
    re_path(r'^graph/(?P<pk>\d+)/bare/original/$', get_graph, {'bare': True, 'original': True}, name='show-bare-graph'),
]
