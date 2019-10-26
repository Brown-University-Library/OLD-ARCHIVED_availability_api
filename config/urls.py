# -*- coding: utf-8 -*-

from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic import RedirectView
from availability_app import views as avl_views


admin.autodiscover()

urlpatterns = [

    ## primary app urls...
    url( r'^v1/(?P<id_type>.*)/(?P<id_value>.*)/$', avl_views.ezb_v1, name='ezb_v1_url' ),
    url( r'^v1_stats/$', avl_views.ezb_v1_stats, name='ezb_v1_stats_url' ),
    url( r'^v2/bib_items/(?P<bib_value>.*)/$', avl_views.v2_bib_items, name='v2_bib_items_url' ),
    url( r'^locations_and_statuses/$', avl_views.locations_and_statuses, name='locations_and_statuses_url' ),
    url( r'^admin/', include(admin.site.urls) ),

    ## demo urls...
    url( r'^async/$', avl_views.concurrency_test, name='async_url' ),
    url( r'^v2/bib_items_async/(?P<bib_value>.*)/$', avl_views.v2_bib_items_async, name='v2_bib_items_async_url' ),

    ## support urls...
    url( r'^info/$',  avl_views.version, name='info_url' ),  # historical url
    url( r'^version/$',  avl_views.version, name='version_url' ),  # newer url endpoint
    url( r'^error_check/$',  avl_views.error_check, name='error_check_url' ),

    url( r'^$',  RedirectView.as_view(pattern_name='info_url') ),

    ]
