# -*- coding: utf-8 -*-

from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic import RedirectView
from availability_app import views as avl_views


admin.autodiscover()

urlpatterns = [

    url( r'^admin/', include(admin.site.urls) ),  # eg host/project_x/admin/

    # url( r'^', include('availability_app.urls_app') ),  # eg host/project_x/anything/

    url( r'^info/$',  avl_views.hi, name='info_url' ),

    url( r'^v2/(?P<id_type>.*)/(?P<id_value>.*)/$',  avl_views.handler, name='handler_url' ),  # id_type, 'isbn' or 'oclc'

    url( r'^$',  RedirectView.as_view(pattern_name='info_url') ),

    ]
