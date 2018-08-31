# -*- coding: utf-8 -*-

"""
Helper for views.ezb_v1_stats()
"""

import datetime, json, logging, os, pickle, pprint, subprocess
from availability_app import settings_app
from django.core.cache import cache
from django.core.urlresolvers import reverse

log = logging.getLogger(__name__)


class StatsBuilder( object ):
    """ Handles stats-api calls. """

    def __init__( self ):
        self.date_start = None  # set by check_params()
        self.date_end = None  # set by check_params()
        self.output = None  # set by check_params()

    def check_params( self, get_params, scheme, host, rq_now ):
        """ Checks parameters; returns boolean.
            Called by views.stats_v1() """
        log.debug( 'get_params, `%s`' % get_params )
        if 'start_date' not in get_params or 'end_date' not in get_params:  # not valid
            self._handle_bad_params( scheme, host, get_params, rq_now )
            return False
        else:  # valid
            self.date_start = '%s 00:00:00' % get_params['start_date']
            self.date_end = '%s 23:59:59' % get_params['end_date']
            return True

    def _handle_bad_params( self, scheme, host, get_params, rq_now ):
        """ Prepares bad-parameters data.
            Called by check_params() """
        data = {
            'request': {
                'date_time': str( datetime.datetime.now() ),
                'query': '%s://%s%s%s' % ( scheme, host, reverse('ezb_v1_stats_url'), self._prep_querystring(get_params) ) },
            'response': {
                'status': '400 / Bad Request',
                'message': 'example url: %s://%s%s?start_date=2018-07-01&end_date=2018-07-31' % ( scheme, host, reverse('ezb_v1_stats_url') ),
                'time_taken': str( datetime.datetime.now() - rq_now ) }
            }
        self.output = json.dumps( data, sort_keys=True, indent=2 )
        return

    def _prep_querystring( self, get_params ):
        """ Makes querystring from params.
            Called by _handle_bad_params() """
        if get_params:
            querystring = '?%s' % get_params.urlencode()  # get_params is a django QueryDict object, which has a urlencode() method! yay!
        else:
            querystring = ''
        return querystring

    ## end StatsBuilder()
