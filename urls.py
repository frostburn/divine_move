from django.conf.urls import url, include
from django.views.generic import RedirectView
from django.contrib.auth import views as auth_views

from . import views
from . import tsumego_views

urlpatterns = [
    url(r'^clear_session/$',views.clear_session, name='clear_session'),
    url(r'^logout/$', views.logout, name='logout'),  # Redirects to admin views otherwise.
    url(r'^', include('django.contrib.auth.urls')),
    url(r'^signup/$', views.signup, name='signup'),
    url(r'^accounts/profile/$', views.ProfileView.as_view(), name='profile'),
    url(r'^accounts/login/$', RedirectView.as_view(url='/login/', permanent=False)),
    url(r'^favicon\.ico$', RedirectView.as_view(url='/static/img/favicon.ico', permanent=False)),
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
    url(r'^json/go9x9/game/(?P<code>[a-zA-Z0-9_-]+)/(?P<game_num>[0-9]+)/$', views.Go9x9JSONGameView.as_view(), name='go9x9_game_json'),
    url(r'^api/go9x9/add_sgf/$', views.go9x9_add_sgf, name='go9x9_sgf_api'),
    url(r'^faq/go9x9/$', views.Go9x9FAQView.as_view(), name='go9x9_faq'),
    url(r'^tsumego/$', tsumego_views.TsumegoIndexView.as_view(), name='tsumego_index'),
    url(r'^tsumego/reset/$', tsumego_views.TsumegoResetView.as_view(), name='tsumego_reset'),
    url(r'^tsumego/problems/$', tsumego_views.TsumegoProblemIndexView.as_view(), name='tsumego_problems'),
    url(r'^tsumego/(?P<name>[a-zA-Z0-9_-]+)/$', tsumego_views.TsumegoEmptyView.as_view(), name='tsumego_empty'),
    url(r'^tsumego/(?P<name>[a-zA-Z0-9_-]+)/(?P<code>[a-zA-Z0-9_-]+)/$', tsumego_views.TsumegoView.as_view(), name='tsumego'),
    url(r'^tsumego/problems/(?P<name>[a-zA-Z0-9_-]+)/(?P<code>[a-zA-Z0-9_-]+)/$', tsumego_views.TsumegoProblemView.as_view(), name='tsumego_problem'),
    url(r'^json/tsumego/(?P<name>[a-zA-Z0-9_-]+)/$', tsumego_views.TsumegoJSONView.as_view(), name='tsumego_json'),
    url(r'^$', views.IndexView.as_view(), name='index'),
]
