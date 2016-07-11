from django.conf.urls import include, url
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),

    url(r'^logout/$', views.logout_view, name='logout_view'),
    url(r'^', include('django.contrib.auth.urls')),
]
