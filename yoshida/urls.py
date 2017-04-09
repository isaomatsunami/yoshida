# coding: utf-8

from django.conf.urls import url
from django.conf import settings
from django.conf.urls.static import static

from yoshida import views as yoshida_views

urlpatterns = [
    # html
    url(r'^$', yoshida_views.main, name='main'),
    url(r'^document/(?P<document_id>.*)$', yoshida_views.document, name='document'),
    url(r'^page/(?P<page_id>.*)$', yoshida_views.page, name='page'),
    url(r'^text/(?P<document_id>.*)$', yoshida_views.text, name='text'),
    # RESTful
    url(r'^api/lineinfos/(?P<id>.*)$', yoshida_views.lineinfo, name='lineinfo'),
    url(r'^api/pageinfos/(?P<id>.*)$', yoshida_views.pageinfo, name='pageinfo'),
] + static(settings.STATIC_URL, document_root='yoshida/static/')
