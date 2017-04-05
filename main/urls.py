from django.conf.urls import url
from main import views
from django.views.generic import RedirectView

urlpatterns = [
    url(r'^$', views.default, name='default'),
    url(r'^view/?$', RedirectView.as_view(url = r'/')),
    url(r'^view/(?P<cuid>[0-9a-zA-Z]+)/?$', views.CustDetails.as_view(), name='CustDetails'),
    url(r'^count/?$', views.CustomerCount.as_view(), name='CustomerCount'),
    url(r'^spago/(?P<cuid>[0-9a-zA-Z]+)/?$', views.SpagoDetails.as_view(), name='SpagoDetails'),
    url(r'^client/?$', views.RetrieveRefreshToken.as_view(), name='RefreshToken'),
]