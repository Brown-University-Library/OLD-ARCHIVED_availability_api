# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import datetime, json, logging, os, pprint

from availability_app.utils.app_helper import HandlerHelper
from availability_app import settings_app
from django.conf import settings as project_settings
from django.contrib.auth import logout
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render

log = logging.getLogger(__name__)
helper = HandlerHelper( settings_app.Z_HOST, settings_app.Z_PORT, settings_app.Z_TYPE )


def hi( request ):
    """ Returns simplest response. """
    log.debug( 'starting hi()' )
    now = datetime.datetime.now()
    return HttpResponse( '<p>hi</p> <p>( {} )</p>'.format(unicode(now)) )


def handler( request, id_type, id_value ):
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
