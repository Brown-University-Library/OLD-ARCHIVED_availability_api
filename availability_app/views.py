# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import datetime, json, logging, os, pprint

from availability_app.utils.app_helper import HandlerHelper
from django.conf import settings as project_settings
from django.contrib.auth import logout
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render

log = logging.getLogger(__name__)
helper = HandlerHelper()


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
        flask.request.url, key, value, flask.request.args.get(u'show_marc', u'') )
    validation = helper.validate( key, value )
    if not validation == u'good':
        return_dict = { u'query': query, u'response': {u'error': validation} }
        return flask.jsonify( return_dict )
    response = helper.build_response_dict(
        key, value, flask.request.args.get(u'show_marc', u'') )
    return flask.jsonify( {u'query': query, u'response': response} )


    # now = datetime.datetime.now()
    # return HttpResponse( '<p>hi</p> <p>( {} )</p>'.format(unicode(now)) )
