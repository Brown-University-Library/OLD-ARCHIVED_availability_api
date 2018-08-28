# -*- coding: utf-8 -*-

"""
Helper for views.handler()
"""

import datetime, json, logging, os, pickle, pprint, subprocess
import pymarc
from availability_app import settings_app

log = logging.getLogger(__name__)


class EzbV1Helper( object ):
    """ Helper for v1 api route. """

    def __init__( self ):
        log.debug( 'initializing helper' )
        # self.legit_services = [ 'isbn', 'oclc' ]
        self.legit_services = [ 'bib', 'isbn', 'oclc' ]
        self.parser = Parser()
        self.ezb_requestable_locations = None
        self.ezb_requestable_statuses = None

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
        data_dct = { 'request': self.build_query_dict( request, rq_now ), 'response': {'basics': 'init', 'sierra': 'init', 'time_taken': 'init'} }
        pickled_data = self.query_josiah( key, value, show_marc_param )
        assert type(pickled_data) == bytes, 'type(pickled_data), %s' % type(pickled_data)
        unpickled_data = pickle.loads( pickled_data )
        log.debug( 'unpickled_data, ```%s```' % pprint.pformat(unpickled_data) )
        data_dct['response']['sierra'] = self.build_holdings_dct( unpickled_data )
        data_dct['response']['basics'] = self.build_summary_dct( data_dct['response']['sierra'] )
        data_dct['response']['time_taken'] = str( datetime.datetime.now() - rq_now )
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
        summary_dct = { 'ezb_requestable_bibs': [] }
        # summary_dct['title'] = sierra_holdings[0]['title']
        summary_dct['ezb_requestable_bibs'] = self.determine_ezb_requestability( sierra_holdings )
        log.debug( 'summary_dct, ```%s```' % pprint.pformat(summary_dct) )
        return summary_dct

    def determine_ezb_requestability( self, sierra_holdings ):
        """ Returns boolean for easyBorrow requestability.
            Called by build_summary_dct() """
        self.prep_ezb_requestable_locations()
        self.prep_ezb_requestable_statuses()
        requestable_bibs = []
        for item in sierra_holdings:
            for holding_info in item['holdings']:
                if holding_info['localLocation'] in self.ezb_requestable_locations and holding_info['publicNote'] in self.ezb_requestable_statuses:
                    # requestable_bibs.append( 'https://search.library.brown.edu/catalog/%s' % item['bib'] )
                    requestable_bibs.append( {
                        'title': item['title'], 'url': 'https://search.library.brown.edu/catalog/%s' % item['bib']
                        } )
                    break
        log.debug( 'requestable_bibs, ```%s```' % pprint.pformat(requestable_bibs) )
        return requestable_bibs

    def prep_ezb_requestable_locations( self ):
        """ Populates ezb_requestable_locations.
            Called by __init__()
            TODO: load from editable admin-db. """
        ezb_requestable_locations = [
            'ANNEX',
            'ORWIG STORAGE',
            'ORWIG',
            'ROCK CHINESE',
            'ROCK JAPANESE',
            'ROCK KOREAN',
            'ROCK STORAGE CUTTER',
            'ROCK STORAGE FARMINGTON',
            'ROCK STORAGE STAR',
            'ROCK STORAGE TEXTBOOKS',
            'ROCK STORAGE THESES',
            'ROCK STORAGE',
            'ROCK',
            'SCI THESES'
            'SCI',
        ]
        log.debug( 'ezb_requestable_locations, ```%s```' % ezb_requestable_locations )
        self.ezb_requestable_locations = ezb_requestable_locations
        return

    def prep_ezb_requestable_statuses( self ):
        """ Populates ezb_requestable_statuses.
            Called by __init__()
            TODO: load from editable admin-db. """
        ezb_requestable_statuses = [
            'AVAILABLE',
            'NEW BOOKS',
            'USE IN LIBRARY',
            'ASK AT CIRC',
        ]
        log.debug( 'ezb_requestable_statuses, ```%s```' % ezb_requestable_statuses )
        self.ezb_requestable_statuses = ezb_requestable_statuses
        return

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

    # def make_bibid( self, pymrc_rcrd ):
    #     """ Parses bib.
    #         Called by EzbV1Helper.build_holdings_dct()
    #         TODO: try record-get_field() method; should be quicker. """
    #     marc_dict = pymrc_rcrd.as_dict()
    #     bibid = 'bibid_not_available'
    #     for field in marc_dict['fields']:
    #         ( key, val ) = list( field.items() )[0]
    #         if key == '907':
    #             for subfield in field[key][u'subfields']:
    #                 ( key2, val2 ) = list( subfield.items() )[0]
    #                 if key2 == 'a':
    #                     bibid = val2
    #                     break
    #     bibid = bibid.replace( '.', '' )
    #     log.debug( 'bibid, `%s`' % bibid )
    #     return bibid

    ## end Parser()
