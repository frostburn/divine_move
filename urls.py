from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^go/$', views.GoIndexView.as_view(), name='go_index'),
    url(r'^go/(?P<endgame_type>[a-z0-9]+)/$', views.GoEmptyView.as_view(), name='go_empty'),
    url(r'^go/(?P<endgame_type>[a-z0-9]+)/(?P<endgame>[a-z0-9]+)/$', views.GoView.as_view(), name='go'),
    url(r'^json/go/(?P<endgame_type>[a-z0-9]+)/(?P<endgame>[a-z0-9]+)/$', views.GoJSONView.as_view(), name='go_json'),
    url(r'^$', views.IndexView.as_view(), name='index'),
]
