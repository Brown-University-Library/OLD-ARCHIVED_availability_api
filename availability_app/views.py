# -*- coding: utf-8 -*-

import datetime, json, logging, os, pprint

from availability_app.lib.app_helper import HandlerHelper
from availability_app import settings_app
from django.conf import settings as project_settings
from django.contrib.auth import logout
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render

log = logging.getLogger(__name__)
helper = HandlerHelper( settings_app.Z_HOST, settings_app.Z_PORT, settings_app.Z_TYPE )


def info( request ):
    """ Returns simplest response. """
    log.debug( 'starting info()' )
    now = datetime.datetime.now()
    return HttpResponse( '<p>time: %s</p>' % str(now) )


def ezb_v1( request, id_type, id_value ):
    """ Handles existing easyborrow-api call. """
    params = request.GET
    log.debug( 'starting; id_type, `{}`; id_value, `{}`; get, `{}`'.format(id_type, id_value, pprint.pformat(params)) )
    # helper = app_helper.HandlerHelper()
    query = helper.build_query_dict(
        request.META.get('QUERY_STRING', ''), id_type, id_value, request.GET.get('show_marc', '') )
    validation = helper.validate( id_type, id_value )
    if not validation == u'good':
        return_dict = { u'query': query, u'response': {u'error': validation} }
        jsn = json.dumps( return_dict, sort_keys=True, indent=2 )
    else:
        response = helper.build_response_dict( id_type, id_value, request.GET.get('show_marc', '') )
        jsn = json.dumps( {u'query': query, u'response': response}, sort_keys=True, indent=2 )
    return HttpResponse( jsn, content_type='application/javascript; charset=utf-8' )


def ezb_v2( request, id_type, id_value ):
    """ Handles upcoming easyborrow-api call. """
    return HttpResponse( 'ezb_v2_url handling coming' )
