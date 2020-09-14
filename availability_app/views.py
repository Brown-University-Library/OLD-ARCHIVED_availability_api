# -*- coding: utf-8 -*-

import datetime, json, logging, os, pprint

from availability_app import settings_app
from availability_app.lib import view_info_helper
from availability_app.lib.concurrency import AsyncHelper  # temporary demo helper
from availability_app.lib.ezb_v1_handler import EzbV1Helper
from availability_app.lib.bib_items_v2 import BibItemsInfo
from availability_app.lib.bib_items_async_v2 import BibItemsInfoAsync  # not yet in production
from availability_app.lib.stats_v1_handler import StatsValidator, StatsBuilder
from django.conf import settings as project_settings
from django.contrib.auth import logout
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseBadRequest, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render


log = logging.getLogger( __name__ )
slog = logging.getLogger( 'stats_logger' )
ezb1_helper = EzbV1Helper()
stats_builder = StatsBuilder()
stats_validator = StatsValidator()
bib_items = BibItemsInfo()


# ===========================
# demo handlers
# ===========================


def concurrency_test( request ):
    """ Tests concurrency, via trio, with django. """
    if project_settings.DEBUG == False:  # only active on dev-server
        return HttpResponseNotFound( '<div>404 / Not Found</div>' )
    async_hlpr = AsyncHelper()
    url_dct = {
        'shortest': 'https://httpbin.org/delay/.6',
        'shorter': 'https://httpbin.org/delay/.8',
        'standard': 'https://httpbin.org/delay/1',
        'longer': 'https://httpbin.org/delay/1.2',
        'longest': 'https://httpbin.org/delay/1.4' }
    if request.GET.get( 'outlier', '' ) == 'yes':
        url_dct['outlier'] = 'https://httpbin.org/delay/10'
    async_hlpr.process_urls( url_dct )
    response_dct = { 'results:': async_hlpr.results_dct, 'total_time_taken': async_hlpr.total_time_taken }
    output = json.dumps( response_dct, sort_keys=True, indent=2 )
    return HttpResponse( output, content_type='application/json; charset=utf-8' )


def v2_bib_items_async( request, bib_value ):
    """ Not currently used; non-async version in production is used by easyrequest_hay. """
    # if project_settings.DEBUG == False:  # only active on dev-server
    #     return HttpResponseNotFound( '<div>404 / Not Found</div>' )
    bib_items_async = bitems_async = BibItemsInfoAsync()
    log.debug( f'starting... request.__dict__, ```{request.__dict__}```' )
    start_stamp = datetime.datetime.now()
    query_dct = bitems_async.build_query_dct( request, start_stamp )
    raw_data_dct = bitems_async.manage_data_calls( bib_value )
    host = request.META.get( 'HTTP_HOST', '127.0.0.1' )
    data_dct = bitems_async.prep_data( raw_data_dct, host )
    response_dct = bitems_async.build_response_dct( data_dct, start_stamp )
    jsn = json.dumps( { 'query': query_dct, 'response': response_dct }, sort_keys=True, indent=2 )
    return HttpResponse( jsn, content_type='application/javascript; charset=utf-8' )


# ===========================
# primary app handlers
# ===========================


def ezb_v1( request, id_type, id_value ):
    """ Handles existing easyborrow-api call. """
    params = request.GET
    log.debug( 'starting; id_type, `%s`; id_value, `%s`' % (id_type, id_value) )
    validity_dct = ezb1_helper.validate( id_type, id_value )
    if validity_dct['validity'] is not True:
        data_dct = { 'query': ezb1_helper.build_query_dct( request, datetime.datetime.now() ), u'response': {u'error': validity_dct['error']} }
        jsn = json.dumps( data_dct, sort_keys=True, indent=2 )
        return HttpResponseBadRequest( jsn, content_type=u'application/javascript; charset=utf-8' )
    else:
        data_dct = ezb1_helper.build_data_dct( id_type, validity_dct['value'], request.GET.get('show_marc', ''), request )
        jsn = json.dumps( data_dct, sort_keys=True, indent=2 )
        return HttpResponse( jsn, content_type='application/javascript; charset=utf-8' )


def v2_bib_items( request, bib_value ):
    """ Handles easy_request_hay call. """
    # log.debug( f'starting... request.__dict__, ```{pprint.pformat(request.__dict__)}```' )
    log.debug( f'starting... request.__dict__, ```{request.__dict__}```' )
    start_stamp = datetime.datetime.now()
    query_dct = bib_items.build_query_dct( request, start_stamp )
    host = request.META.get( 'HTTP_HOST', '127.0.0.1' )
    data_dct = bib_items.prep_data( bib_value, host )
    ## TODO- refactor this quick-handling of a bad sierra response
    response_dct = {}
    if 'httpStatus' in data_dct.keys():
        if data_dct['httpStatus'] != 200:
            response_dct = { 'problem_sierra_response': data_dct }
            jsn = json.dumps( { 'query': query_dct, 'response': response_dct }, sort_keys=True, indent=2 )
            return HttpResponseNotFound( jsn, content_type='application/javascript; charset=utf-8' )
    else:
        response_dct = bib_items.build_response_dct( data_dct, start_stamp )
        jsn = json.dumps( { 'query': query_dct, 'response': response_dct }, sort_keys=True, indent=2 )
        return HttpResponse( jsn, content_type='application/javascript; charset=utf-8' )


def ezb_v1_stats( request ):
    """ Returns basic stats on v1-api usage. """
    log.debug( 'starting ezb_v1_stats()' )
    slog.info( 'new entry!' )
    ## grab & validate params
    rq_now = datetime.datetime.now()
    if stats_validator.check_params( request.GET, request.scheme, request.META['HTTP_HOST'], rq_now ) == False:
        return HttpResponseBadRequest( stats_validator.output, content_type=u'application/javascript; charset=utf-8' )
    ## run-query
    results = stats_builder.run_query( request.GET )
    ## build response
    stats_builder.build_response( results, request.GET, request.scheme, request.META['HTTP_HOST'], rq_now )
    return HttpResponse( stats_builder.output, content_type=u'application/javascript; charset=utf-8' )


def locations_and_statuses( request ):
    """ Shows values being used. """
    rq_now = datetime.datetime.now()
    data_dct = {
        'query': ezb1_helper.build_query_dct( request, rq_now ),
        'response': {
            'ezb_available_locations': json.loads( os.environ['AVL_API__EZB_AVAILABLE_LOCATIONS'] ),
            'ezb_available_statuses': json.loads( os.environ['AVL_API__EZB_AVAILABLE_STATUSES'] ),
            'time_taken': str( datetime.datetime.now() - rq_now ) }
    }
    output = json.dumps( data_dct, sort_keys=True, indent=2 )
    return HttpResponse( output, content_type='application/json; charset=utf-8' )


# ===========================
# for development convenience
# ===========================


def version( request ):
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


def error_check( request ):
    """ For checking that admins receive error-emails. """
    if project_settings.DEBUG == True:
        1/0
    else:
        return HttpResponseNotFound( '<div>404 / Not Found</div>' )
