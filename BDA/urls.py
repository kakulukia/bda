"""BDA URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
from rest_framework import routers
from rest_framework_swagger.views import get_swagger_view

from areas.views import BioListView, AreaBioView, add_bio, AreaBioViewSet

# Routers provide an easy way of automatically determining the URL conf.
router = routers.DefaultRouter()
router.register(r'area-bio', AreaBioViewSet)


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
    url(r'^graph/(?P<pk>[\w-]+)/', AreaBioView.as_view(), name='detail'),
]
