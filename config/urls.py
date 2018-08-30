# -*- coding: utf-8 -*-

from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic import RedirectView
from availability_app import views as avl_views


admin.autodiscover()

urlpatterns = [

    # url( r'^admin/', include(admin.site.urls) ),

    url( r'^info/$',  avl_views.info, name='info_url' ),

    url( r'^v1/(?P<id_type>.*)/(?P<id_value>.*)/$',  avl_views.ezb_v1, name='ezb_v1_url' ),

    url( r'^v2/(?P<id_type>.*)/(?P<id_value>.*)/$',  avl_views.ezb_v2, name='ezb_v2_url' ),

    url( r'^locations_and_statuses/$',  avl_views.locations_and_statuses, name='locations_and_statuses_url' ),

    url( r'^$',  RedirectView.as_view(pattern_name='info_url') ),

    ]
