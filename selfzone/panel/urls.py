from django.conf.urls import include, url
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic.edit import CreateView
from django.contrib.auth.forms import UserCreationForm
from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^ordered/(?P<type>(score|older|newer))$', views.index_ordered, name='index_ordered'),

    url(r'^logout/$', views.logout_view, name='logout_view'),
    url(r'^', include('django.contrib.auth.urls')),
    url(r'^register/ok$', views.register_ok, name='register_ok'),
    url(r'^register/$', CreateView.as_view(template_name='registration/register.html',
                                          form_class=UserCreationForm,
                                          success_url='/selfzone/panel/register/ok'), name="register"),
]
