# -*- coding: utf-8 -*-

import datetime, json, logging, os, pprint

from availability_app import settings_app
from availability_app.lib import view_info_helper
from availability_app.lib.ezb_v1_handler import EzbV1Helper
from availability_app.lib.stats_v1_handler import StatsValidator
from django.conf import settings as project_settings
from django.contrib.auth import logout
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render


log = logging.getLogger(__name__)
ezb1_helper = EzbV1Helper()
stats_validator = StatsValidator()


def info( request ):
    """ Returns basic data including branch & commit. """
    # log.debug( 'request.__dict__, ```%s```' % pprint.pformat(request.__dict__) )
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
        data_dct = { 'query': query, u'response': {u'error': validation} }
    else:
        data_dct = ezb1_helper.build_data_dct( id_type, id_value, request.GET.get('show_marc', ''), request )
    jsn = json.dumps( data_dct, sort_keys=True, indent=2 )
    return HttpResponse( jsn, content_type='application/javascript; charset=utf-8' )


def ezb_v1_stats( request ):
    """ Returns basic stats on v1-api usage. """
    ## grab & validate params
    rq_now = datetime.datetime.now()
    if stats_validator.check_params( request.GET, request.scheme, request.META['HTTP_HOST'], rq_now ) == False:
        return HttpResponseBadRequest( stats_validator.output, content_type=u'application/javascript; charset=utf-8' )
    return HttpResponse( 'ezb_v1_stats handling coming' )
    ## run-query
    results = stats_builder.run_query( request.GET )
    ## build response
    stats_builder.build_response( results, request.GET, request.scheme, request.META['HTTP_HOST'], rq_now )
    return HttpResponse( stats_builder.output, content_type=u'application/javascript; charset=utf-8' )


def ezb_v2( request, id_type, id_value ):
    """ Handles upcoming easyborrow-api call. """
    return HttpResponse( 'ezb_v2_url handling coming' )


def locations_and_statuses( request ):
    """ Shows values being used. """
    rq_now = datetime.datetime.now()
    data_dct = {
        'query': ezb1_helper.build_query_dict( request, rq_now ),
        'response': {
            'ezb_available_locations': json.loads( os.environ['AVL_API__EZB_AVAILABLE_LOCATIONS'] ),
            'ezb_available_statuses': json.loads( os.environ['AVL_API__EZB_AVAILABLE_STATUSES'] ),
            'time_taken': str( datetime.datetime.now() - rq_now ) }
    }
    output = json.dumps( data_dct, sort_keys=True, indent=2 )
    return HttpResponse( output, content_type='application/json; charset=utf-8' )
