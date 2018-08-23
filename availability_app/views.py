# -*- coding: utf-8 -*-

import datetime, json, logging, os, pprint

from availability_app import settings_app
from availability_app.lib import view_info_helper
from availability_app.lib.ezb_v1_handler import EzbV1Helper
from django.conf import settings as project_settings
from django.contrib.auth import logout
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render


log = logging.getLogger(__name__)
ezb1_helper = EzbV1Helper()


# def info( request ):
#     """ Returns simplest response. """
#     log.debug( 'starting info()' )
#     now = datetime.datetime.now()
#     return HttpResponse( '<p>time: %s</p>' % str(now) )


def info( request ):
    """ Returns basic data including branch & commit. """
    rq_now = datetime.datetime.now()
    commit = view_info_helper.get_commit()
    branch = view_info_helper.get_branch()
    info_txt = commit.replace( 'commit', branch )
    resp_now = datetime.datetime.now()
    taken = resp_now - rq_now
    context_dct = view_info_helper.make_context( request, rq_now, info_txt, taken )
    output = json.dumps( context_dct, sort_keys=True, indent=2 )
    return HttpResponse( output, content_type='application/json; charset=utf-8' )


def ezb_v1( request, id_type, id_value ):
    """ Handles existing easyborrow-api call. """
    params = request.GET
    log.debug( 'starting; id_type, `%s`; id_value, `%s`' % (id_type, id_value) )
    validation = ezb1_helper.validate( id_type, id_value )
    if not validation == 'good':
        return_dict = { 'query': query, u'response': {u'error': validation} }
        jsn = json.dumps( return_dict, sort_keys=True, indent=2 )
    else:
        response = ezb1_helper.build_response_dict( id_type, id_value, request.GET.get('show_marc', '') )
        jsn = json.dumps( response, sort_keys=True, indent=2 )
    return HttpResponse( jsn, content_type='application/javascript; charset=utf-8' )


def ezb_v2( request, id_type, id_value ):
    """ Handles upcoming easyborrow-api call. """
    return HttpResponse( 'ezb_v2_url handling coming' )
