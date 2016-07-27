from django.conf.urls import url, include
from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^old/(?P<old1_id>[0-9]+)vs(?P<old2_id>[0-9]+)=(?P<voted>(left|right))$', views.index_voted, name='index_voted'),
    url(r'^upload/$', views.upload, name='upload'),
    url(r'^vote/(?P<s1_id>[0-9]+)vs(?P<s2_id>[0-9]+)=(?P<voted>(left|right))$', views.vote, name='vote'),
    url(r'^details/(?P<selfie_id>[0-9]+)', views.details, name='details'),
    url(r'^stats', views.stats, name='stats'),
    url(r'^top/(?P<num>[0-9]*)$', views.top, name='top'),
    url(r'^bottom/(?P<num>[0-9]*)$', views.bottom, name='bottom'),
    url(r'^top/(?P<year>[0-9]+)/(?P<month>[0-9]+)/(?P<day>[0-9]+)/(?P<num>[0-9]*)$', views.top_day, name='top'),
    url(r'^bottom/(?P<year>[0-9]+)/(?P<month>[0-9]+)/(?P<day>[0-9]+)/(?P<num>[0-9]*)$', views.bottom_day, name='bottom'),
    url(r'^top/(?P<year>[0-9]+)/(?P<week>[0-9]+)/(?P<num>[0-9]*)$', views.top_week, name='top'),
    url(r'^bottom/(?P<year>[0-9]+)/(?P<week>[0-9]+)/(?P<num>[0-9]*)$', views.bottom_week, name='bottom'),

    url(r'^panel/', include('selfzone.panel.urls', namespace="selfzone.panel")),
]