# -*- coding: utf-8 -*-

"""
Helper for views.handler()
"""

import datetime, json, logging, os, pickle, pprint, subprocess
import pymarc
from availability_app import settings_app

log = logging.getLogger(__name__)


class EzbV1Helper( object ):
    """ Helpers for main api route: availability_service.availability_app.handler() """

    # def __init__( self, z_host, z_port, z_type ):
    #     # self.log = log
    #     self.HOST = z_host
    #     self.PORT = z_port
    #     self.DB_NAME = z_type
    #     self.legit_services = [ u'bib', u'isbn', u'issn', u'oclc' ]  # will enhance; possible TODO: load from yaml config file
    #     # self.cache_dir = os.getenv( u'availability_CACHE_DIR' )
    #     # self.cache_minutes = int( os.getenv(u'availability_CACHE_MINUTES') ) * 60  # timeout param requires seconds

    def __init__( self ):
        self.legit_services = [ 'isbn', 'oclc' ]

    def validate( self, key, value ):
        """ Stub for validation. IP checking another possibility.
            Called by availability_service.availability_app.handler(). """
        message = u'init'
        if key not in self.legit_services:
            message = 'query_key bad'
        if message == 'init':
            message = 'good'
        log.debug( 'message, {}'.format(message) )
        return message

    def build_data_dct( self, key, value, show_marc_param, request ):
        """ Manager for z39.50 query, and result-processor.
            Called by views.ezb_v1(). """
        rq_now = datetime.datetime.now()
        data_dct = { 'request': self.build_query_dict( request, rq_now ), 'response': {} }
        pickled_data = self.query_josiah( key, value, show_marc_param )
        assert type(pickled_data) == bytes, 'type(pickled_data), %s' % type(pickled_data)
        unpickled_data = pickle.loads( pickled_data )
        log.debug( 'unpickled_data, ```%s```' % pprint.pformat(unpickled_data) )
        data_dct['response'] = self.build_response_dict( unpickled_data )
        return data_dct

    def query_josiah( self, key, value, show_marc_param ):
        """ Perform actual query.
            Called by self.build_data_dct(). """
        log.debug( 'starting query_josiah()' )
        cmd_1 = 'cd %s' % ( settings_app.CMD_START_DIR_PATH )
        cmd_2 = 'source %s/activate' % ( settings_app.CMD_ENV_BIN_DIR_PATH )
        cmd_3 = '%s/python2 %s/py2_z3950_wrapper.py --key %s --value %s' % ( settings_app.CMD_ENV_BIN_DIR_PATH, settings_app.CMD_WRAPPER_DIR_PATH, key, value )
        py3_cmd = cmd_1 + '; ' + cmd_2 + '; ' + cmd_3
        log.debug( 'py3_cmd, ```%s```' % py3_cmd )
        process = subprocess.Popen( py3_cmd, shell=True, stdout=subprocess.PIPE )
        output, error = process.communicate()  # receive output from the python2 script
        log.debug( 'output, ```%s```; error, ```%s```' % (output, error) )
        return output

    def build_query_dict( self, request, rq_now ):
        query_dct = {
            'url': '%s://%s%s' % ( request.scheme,
                request.META.get( 'HTTP_HOST', '127.0.0.1' ),  # HTTP_HOST doesn't exist for client-tests
                request.META.get('REQUEST_URI', request.META['PATH_INFO'])
                ),
            'timestamp': str( rq_now )
            }
        log.debug( 'query_dct, ```%s``' % pprint.pformat(query_dct) )
        return query_dct

    def build_response_dict( self, unpickled_dct ):
        """ Processes z3950 data into response.
            Called by build_data_dct() """
        items = []
        z_items = unpickled_dct['backend_response']
        for ( i, z_item ) in enumerate( z_items ):
            pymrc_obj = z_item['pymarc_obj']
            log.debug( 'pymrc_obj.__dict__, ```%s```' % pprint.pformat(pymrc_obj.__dict__) )
            holdings = z_item['holdings_data']
            item_dct = { 'title': pymrc_obj.title(), 'holdings': holdings }
            items.append( item_dct )
        log.debug( 'items, ```%s```' % items )
        return items

    # def build_response_dict( self, unpickled_dct ):
    #     """ Processes z3950 data into response.
    #         Called by build_data_dct() """
    #     items = []
    #     z_items = unpickled_dct['backend_response']
    #     for z_item in z_items:
    #         pymrc_obj = z_item['pymarc_obj']
    #         pymrc_dct = pymrc_obj.as_dict()
    #         log.debug( 'pymrc_dct, ```%s```' % pprint.pformat(pymrc_dct) )
    #         items.append( pymrc_dct )
    #     log.debug( 'items, ```%s```' % items )
    #     return items

    # def build_response_dict( self, key, value, show_marc_param ):
    #     """ Handler for cached z39.50 call and response.
    #         Called by availability_service.availability_app.handler(). """
    #     assert type(value) == unicode
    #     cache = FileSystemCache( self.cache_dir, threshold=500, default_timeout=self.cache_minutes, mode=0664 )  # http://werkzeug.pocoo.org/docs/0.9/contrib/cache/
    #     cache_key = u'%s_%s_%s' % ( key, value, show_marc_param )
    #     response_dict = cache.get( cache_key )
    #     if response_dict is None:
    #         self.log.debug( u'in utils.app_helper.HandlerHelper.build_response_dict(); _not_ using cache.' )
    #         response_dict = self.query_josiah( key, value, show_marc_param )
    #         cache.set( cache_key, response_dict )
    #     return response_dict

    ## end class EzbV1Helper()
