from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^go/$', views.GoIndexView.as_view(), name='go_index'),
    url(r'^go/(?P<endgame_type>[a-z0-9]+)/$', views.GoEmptyView.as_view(), name='go_empty'),
    url(r'^go/(?P<endgame_type>[a-z0-9]+)/(?P<endgame>[a-z0-9]+)/$', views.GoView.as_view(), name='go'),
    url(r'^json/go/(?P<endgame_type>[a-z0-9]+)/(?P<endgame>[a-z0-9]+)/$', views.GoJSONView.as_view(), name='go_json'),
    url(r'^chess/$', views.ChessIndexView.as_view(), name='chess_index'),
    url(r'^chess/edit/$', views.ChessEditView.as_view(), name='chess_edit'),
    url(r'^chess/(?P<fen>.+)/$', views.ChessView.as_view(), name='chess'),
    url(r'^json/chess/(?P<fen>.+)/$', views.ChessJSONView.as_view(), name='chess_json'),
    url(r'^go9x9/$', views.Go9x9View.as_view(), name='go9x9_empty'),
    url(r'^go9x9/(?P<code>[a-zA-Z0-9_-]+)/$', views.Go9x9View.as_view(), name='go9x9'),
    url(r'^json/go9x9/(?P<code>[a-zA-Z0-9_-]+)/$', views.Go9x9JSONView.as_view(), name='go9x9_json'),
    url(r'^json/go9x9/end/(?P<code>[a-zA-Z0-9_-]+)/$', views.Go9x9JSONEndView.as_view(), name='go9x9_end_json'),
    url(r'^api/go9x9/add_sgf/$', views.go9x9_add_sgf, name='go9x9_sgf_api'),
    url(r'^$', views.IndexView.as_view(), name='index'),
]
