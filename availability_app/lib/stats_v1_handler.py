# -*- coding: utf-8 -*-

"""
Helper for views.ezb_v1_stats()
"""

import datetime, json, logging, os, pickle, pprint, subprocess
from availability_app import settings_app
from availability_app.models import Tracker
from django.core.cache import cache
from django.core.urlresolvers import reverse

log = logging.getLogger(__name__)


class StatsBuilder( object ):
    """ Queries data and build stats response. """

    def __init__( self ):
        self.output = None
        self.period_start = None
        self.period_end = None
        self.period_start_obj = None
        self.period_end_obj = None

    def run_query( self, get_params_dct ):
        """ Grabs data for period.
            Called by views.ezb_v1_stats() """
        self.period_start = '%s 00:00:00' % get_params_dct['start_date']
        self.period_end = '%s 23:59:59' % get_params_dct['end_date']
        self.period_start_obj = datetime.datetime.strptime( self.period_start, '%Y-%m-%d %H:%M:%S' )
        self.period_end_obj = datetime.datetime.strptime( self.period_end, '%Y-%m-%d %H:%M:%S' )
        # results = {}
        results = Tracker.objects.filter( count_date__gte=self.period_start_obj.date(), count_date__lte=self.period_end_obj.date() ).order_by( 'count_date' )
        # log.debug( 'self.period_start_obj, `%s`' % self.period_start_obj )
        # log.debug( 'self.period_end_obj, `%s`' % self.period_end_obj )
        log.debug( 'results, %s' % pprint.pformat(results) )
        return results

    def build_response( self, results, get_params, scheme, host, rq_now ):
        """ Massages data into response.
            Called by ezb_v1_stats() """
        if results:
            first_record_date = results.first().count_date
            last_record_date = results.last().count_date
            unofficial = 0
            ezb_isbn = 0
            ezb_oclc = 0
            for trckr_entry in results:
                unofficial += trckr_entry.unofficial_access_count
                ezb_isbn += trckr_entry.ezb_isbn_count
                ezb_oclc += trckr_entry.ezb_oclc_count
        else:
            first_record_date = None
            last_record_date = None
            unofficial = 0
            ezb_isbn = 0
            ezb_oclc = 0
        rsp_dct = {
            'request': {
                'date_time': str(rq_now),
                'query': '%s://%s%s%s' % ( scheme, host, reverse('ezb_v1_stats_url'), prep_querystring(get_params) )
            },
            'response': {
                'lookups_ezb': {
                    'oclc_lookup_count': ezb_oclc,
                    'isbn_lookup_count': ezb_isbn
                },
                'lookups_unofficial': unofficial,
                'period': {
                    'first_results_date': str(first_record_date),
                    'last_results_date': str(last_record_date),
                    'query_range': 'from `%s` through `%s`' % ( self.period_start, self.period_end )
                },
                'time_taken': str(datetime.datetime.now() - rq_now)
            }
        }
        log.debug( 'rsp_dct, ```%s```' % pprint.pformat(rsp_dct) )
        self.output = json.dumps( rsp_dct, sort_keys=True, indent = 2 )
        return

    ## end StatsBuilder()


class StatsValidator( object ):
    """ Validates params of stats-api calls. """

    def __init__( self ):
        self.date_start = None  # set by check_params()
        self.date_end = None  # set by check_params()
        self.output = None  # set by check_params()

    def check_params( self, get_params, scheme, host, rq_now ):
        """ Checks parameters; returns boolean.
            Called by views.stats_v1() """
        log.debug( 'get_params, `%s`' % get_params )
        if 'start_date' not in get_params or 'end_date' not in get_params:  # not valid
            self.handle_bad_params( scheme, host, get_params, rq_now )
            return False
        else:  # valid
            self.date_start = '%s 00:00:00' % get_params['start_date']
            self.date_end = '%s 23:59:59' % get_params['end_date']
            return True

    def handle_bad_params( self, scheme, host, get_params, rq_now ):
        """ Prepares bad-parameters data.
            Called by check_params() """
        data = {
            'request': {
                'date_time': str(rq_now),
                'query': '%s://%s%s%s' % ( scheme, host, reverse('ezb_v1_stats_url'), prep_querystring(get_params) ) },
            'response': {
                'status': '400 / Bad Request',
                'message': 'example url: %s://%s%s?start_date=2018-07-01&end_date=2018-07-31' % ( scheme, host, reverse('ezb_v1_stats_url') ),
                'time_taken': str( datetime.datetime.now() - rq_now ) }
            }
        self.output = json.dumps( data, sort_keys=True, indent=2 )
        return

    # def prep_querystring( self, get_params ):
    #     """ Makes querystring from params.
    #         Called by handle_bad_params() """
    #     if get_params:
    #         querystring = '?%s' % get_params.urlencode()  # get_params is a django QueryDict object, which has a urlencode() method! yay!
    #     else:
    #         querystring = ''
    #     return querystring

    ## end StatsValidator()


def prep_querystring( get_params ):
    """ Makes querystring from params.
        Called by handle_bad_params() """
    if get_params:
        querystring = '?%s' % get_params.urlencode()  # get_params is a django QueryDict object, which has a urlencode() method! yay!
    else:
        querystring = ''
    return querystring
