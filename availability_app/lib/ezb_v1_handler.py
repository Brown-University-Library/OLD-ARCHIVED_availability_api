# -*- coding: utf-8 -*-

"""
Helper for views.handler()
"""

import datetime, json, logging, os, pickle, pprint, subprocess, urllib
import pymarc
from availability_app import settings_app
from django.core.cache import cache


log = logging.getLogger(__name__)
slog = logging.getLogger( 'stats_logger' )


class EzbV1Helper( object ):
    """ Helper for v1 api route. """

    def __init__( self ):
        log.debug( 'initializing helper' )
        # self.legit_services = [ 'isbn', 'oclc' ]
        self.legit_services = [ 'bib', 'isbn', 'oclc' ]
        self.parser = Parser()
        self.ezb_available_locations = None
        self.ezb_available_statuses = None

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
        data_dct = { 'request': self.build_query_dct( request, rq_now ), 'response': {'basics': 'init', 'sierra': 'init', 'time_taken': 'init'} }
        pickled_data = self.grab_z3950_data( key, value, show_marc_param )
        assert type(pickled_data) == bytes, 'type(pickled_data), %s' % type(pickled_data)
        unpickled_data = pickle.loads( pickled_data )
        log.debug( 'unpickled_data, ```%s```' % pprint.pformat(unpickled_data) )
        data_dct['response']['sierra'] = self.build_holdings_dct( unpickled_data )
        data_dct['response']['basics'] = self.build_summary_dct( data_dct['response']['sierra'] )
        data_dct['response']['time_taken'] = str( datetime.datetime.now() - rq_now )
        return data_dct

    def grab_z3950_data( self, key, value, show_marc_param ):
        """ Returns data from cache if available; otherwise calls sierra.
            Called by build_data_dct() """
        cache_key = '%s_%s' % (key, value)
        pickled_data = cache.get( cache_key )
        if pickled_data is None:
            log.debug( 'pickled_data was not in cache' )
            pickled_data = self.query_josiah( key, value, show_marc_param )
            cache.set( cache_key, pickled_data )  # time could be last argument; defaults to settings.py entry
        else:
            log.debug( 'pickled_data was in cache' )
        return pickled_data

    def query_josiah( self, key, value, show_marc_param ):
        """ Perform actual query.
            Called by grab_z3950_data(). """
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

    # def build_query_dct( self, request, rq_now ):
    #     query_dct = {
    #         'url': '%s://%s%s' % ( request.scheme,
    #             request.META.get( 'HTTP_HOST', '127.0.0.1' ),  # HTTP_HOST doesn't exist for client-tests
    #             request.META.get('REQUEST_URI', request.META['PATH_INFO'])
    #             ),
    #         'timestamp': str( rq_now )
    #         }
    #     log.debug( 'query_dct, ```%s``' % pprint.pformat(query_dct) )
    #     return query_dct

    # def build_query_dct( self, request, rq_now ):
    #     """ Builds query-dct part of response.
    #         Called by: build_data_dct() """
    #     query_dct = {
    #         'url': '%s://%s%s' % ( request.scheme,
    #             request.META.get( 'HTTP_HOST', '127.0.0.1' ),  # HTTP_HOST doesn't exist for client-tests
    #             request.META.get('REQUEST_URI', request.META['PATH_INFO'])
    #             ),
    #         'timestamp': str( rq_now )
    #         }
    #     log.debug( 'query_dct, ```%s``' % pprint.pformat(query_dct) )
    #     stats_dct = query_dct.copy()
    #     stats_dct['source'] = self.log_source( request )
    #     slog.info( json.dumps(stats_dct) )
    #     return query_dct

    def build_query_dct( self, request, rq_now ):
        """ Builds query-dct part of response.
            Called by: build_data_dct() """
        query_dct = {
            'url': '%s://%s%s' % ( request.scheme,
                request.META.get( 'HTTP_HOST', '127.0.0.1' ),  # HTTP_HOST doesn't exist for client-tests
                request.META.get('REQUEST_URI', request.META['PATH_INFO'])
                ),
            'timestamp': str( rq_now )
            }
        self.build_stats_dct( query_dct['url'], request.META.get('HTTP_REFERER', None), request.META.get('HTTP_USER_AGENT', None) )
        log.debug( 'query_dct, ```%s``' % pprint.pformat(query_dct) )
        return query_dct

    def build_stats_dct( self, query_url, referrer, user_agent ):
        """ Builds and logs data for stats.
            Called by build_query_dct() """
        stats_dct = { 'query': query_url, 'referrer': None, 'user_agent': user_agent }
        if referrer:
            output = urllib.parse.urlparse( referrer )
            stats_dct['referrer'] = output
        slog.info( json.dumps(stats_dct) )
        return

    def build_holdings_dct( self, unpickled_dct ):
        """ Processes z3950 data into response.
            Called by build_data_dct() """
        items = []
        z_items = unpickled_dct['backend_response']
        for z_item in z_items:
            pymrc_obj = z_item['pymarc_obj']
            log.debug( 'pymrc_obj.as_dict(), ```%s```' % pprint.pformat(pymrc_obj.as_dict()) )
            holdings = z_item['holdings_data']
            #
            # log.debug( 'bib?, ```%s```' % pymrc_obj.get_fields('907')[0].format_field() )
            #
            notes_val = []
            notes = pymrc_obj.notes()
            for note in notes:
                notes_val.append( note.format_field() )
            #
            phys_desc_val = []
            physicaldescriptions = pymrc_obj.physicaldescription()
            for phys_desc in physicaldescriptions:
                phys_desc_val.append( phys_desc.format_field() )
            #
            series_val = []
            series_entries = pymrc_obj.series()
            for series in series_entries:
                series_val.append( series.format_field() )
            #
            subjects_val = []
            subjects = pymrc_obj.subjects()
            for subject in subjects:
                subjects_val.append( subject.format_field() )
            #
            item_dct = {
                'bib': self.parser.grab_bib( pymrc_obj ),
                'author': pymrc_obj.author(),
                'isbn': pymrc_obj.isbn(),
                'location': pymrc_obj.location(),
                'notes': notes_val,
                'physicaldescription': phys_desc_val,
                'publisher': pymrc_obj.publisher(),
                'pubyear': pymrc_obj.pubyear(),
                'series': series_val,
                'subjects': subjects_val,
                'title': pymrc_obj.title(),
                'uniformtitle': pymrc_obj.uniformtitle(),
                'holdings': holdings }
            items.append( item_dct )
        log.debug( 'items, ```%s```' % items )
        return items

    def build_summary_dct( self, sierra_holdings ):
        """ Builds simple summary data.
            Called by build_data_dct() """
        self.prep_ezb_available_locations()
        self.prep_ezb_available_statuses()
        summary_dct = { 'ezb_available_bibs': [], 'ezb_available_holdings': [], 'online_holdings': [] }
        summary_dct = self.determine_ezb_requestability( sierra_holdings, summary_dct )
        summary_dct = self.check_online_holdings( sierra_holdings, summary_dct )
        log.debug( 'summary_dct, ```%s```' % pprint.pformat(summary_dct) )
        return summary_dct

    def determine_ezb_requestability( self, sierra_holdings, summary_dct ):
        """ Returns boolean for easyBorrow requestability.
            Called by build_summary_dct() """
        for item in sierra_holdings:
            item_available_holdings = []
            for holding_info in item['holdings']:
                if holding_info['localLocation'] in self.ezb_available_locations and holding_info['publicNote'] in self.ezb_available_statuses:
                    item_available_holdings.append( holding_info )
            if len( item_available_holdings ) > 0:
                summary_dct['ezb_available_holdings'] = summary_dct['ezb_available_holdings'] + item_available_holdings
                bib_dct = { 'bib': item['bib'], 'title': item['title'], 'url': 'https://search.library.brown.edu/catalog/%s' % item['bib'] }
                summary_dct['ezb_available_bibs'].append( bib_dct )
        log.debug( 'summary_dct, ```%s```' % pprint.pformat(summary_dct) )
        return summary_dct

        dict2 = dict1.copy()

    def check_online_holdings( self, sierra_holdings, summary_dct ):
        """ Adds any online holdings to the summary basics dct.
            Called by: build_summary_dct() """
        for item in sierra_holdings:
            for holding_info in item['holdings']:
                if 'online' in holding_info['localLocation'].lower():
                    online_holding_info = holding_info.copy()
                    online_holding_info['title'] = item['title']
                    online_holding_info['url'] = 'https://search.library.brown.edu/catalog/%s' % item['bib']
                    summary_dct['online_holdings'].append( online_holding_info )
        log.debug( 'summary_dct, ```%s```' % pprint.pformat(summary_dct) )
        return summary_dct

    def prep_ezb_available_locations( self ):
        """ Populates ezb_available_locations.
            Called by build_summary_dct()
            TODO: load from editable admin-db. """
        ezb_available_locations = json.loads( os.environ['AVL_API__EZB_AVAILABLE_LOCATIONS'] )
        log.debug( 'ezb_available_locations, ```%s```' % ezb_available_locations )
        self.ezb_available_locations = ezb_available_locations
        return

    def prep_ezb_available_statuses( self ):
        """ Populates ezb_available_statuses.
            Called by build_summary_dct()
            TODO: load from editable admin-db. """
        ezb_available_statuses = json.loads( os.environ['AVL_API__EZB_AVAILABLE_STATUSES'] )
        log.debug( 'ezb_available_statuses, ```%s```' % ezb_available_statuses )
        self.ezb_available_statuses = ezb_available_statuses
        return

    ## end EzbV1Helper()


class Parser( object ):
    """ Parses data from marc. """

    def __init__( self ):
        pass

    def grab_bib( self, pymrc_rcrd ):
        """ Parses bib.
            Called by EzbV1Helper.build_holdings_dct() """
        try:
            bib = pymrc_rcrd['907']['a']
            bib = bib[1:-1]  # removes initial '.', and ending check-digit
        except AttributeError as e:
            log.warning( 'exception getting bib, ```%s```' % e )
            bib = None
        log.debug( 'bib, `%s`' % bib )
        return bib

    ## end Parser()
