# -*- coding: utf-8 -*-

"""
Py2 wrapper for z3950 library call & data-extraction.
Resources:
- z3950 library docs, http://www.panix.com/~asl2/software/PyZ3950/zoom.html
- list of record formats,  http://lists.indexdata.dk/pipermail/zoom/2003-November/000547.html
"""

from __future__ import unicode_literals

import argparse, datetime, json, logging, os, pickle, pprint, sys

assert sys.version_info < ( 3, )

## activate venv
script_dir_path = os.path.dirname(sys.argv[0])
full_script_dir_path = os.path.abspath( script_dir_path )
full_app_dir_path = os.path.dirname( full_script_dir_path )
full_project_dir_path = os.path.dirname( full_app_dir_path )
full_stuff_dir_path = os.path.dirname( full_project_dir_path )
ACTIVATE_FILE = '%s/py2_z3950_stuff/py2env_pyz3950/bin/activate_this.py' % full_stuff_dir_path
# print 'ACTIVATE_FILE path, ```%s```' % ACTIVATE_FILE
execfile( ACTIVATE_FILE, dict(__file__=ACTIVATE_FILE) )

## rest of imports
from PyZ3950 import zoom  # fork, git+https://github.com/Brown-University-Library/PyZ3950.git
from pymarc import Record  # pymarc==3.0.2


## settings
LOG_PATH = os.environ['PY2Z__LOG_PATH']
LOG_LEVEL = os.environ['PY2Z__LOG_LEVEL']
HOST = os.environ['PY2Z__ZHOST']
PORT = os.environ['PY2Z__ZPORT']
DB_NAME = os.environ['PY2Z__ZDB_NAME']


## logging
level_dct = { 'DEBUG': logging.DEBUG, 'INFO': logging.INFO }
logging.basicConfig(
    filename=LOG_PATH,
    level=level_dct[LOG_LEVEL],
    format='[%(asctime)s] %(levelname)s [%(module)s-%(funcName)s()::%(lineno)d] %(message)s', datefmt='%d/%b/%Y %H:%M:%S'
)
log = logging.getLogger(__name__)


class Searcher( object ):

    def __init__( self, HOST, PORT, DB_NAME, connect_flag=False ):
        """ Triggered by py2_z3950_wrapper.query_josiah() """
        self.HOST = HOST   if type(HOST) == unicode   else HOST.decode(u'utf-8')
        self.PORT = PORT   if type(PORT) == unicode   else PORT.decode(u'utf-8')
        self.DB_NAME = DB_NAME   if type(DB_NAME) == unicode   else DB_NAME.decode(u'utf-8')
        # self.logger = log
        self.connection = self.connect()   if connect_flag   else None  # allows Searcher to be instantiated w/o connecting

    def connect( self ):
        """ Connects to z3950 server.
            Called by __init__() """
        conn = zoom.Connection(
            self.HOST,
            int(self.PORT),
            databaseName=self.DB_NAME,
            preferredRecordSyntax=u'OPAC',  # Getting records in "opac" format. (Others were not more helpful.)
            charset='utf-8' )
        log.debug( 'connection made.')
        return conn

    def search( self, key, value, marc_flag=False ):
        """ Convenience function.
            Called by utils.app_helper.HandlerHelper.query_josiah() """
        try:
            qstring = self.build_qstring( key, value )
            qobject = self.build_qobject( qstring )
            resultset = self.connection.search( qobject )
            # import pickle
            items = []
            for result in resultset:
                result_dct = { 'pymarc_obj': None, 'holdings_data': None }
                result_dct['pymarc_obj'] = Record( data=result.data.bibliographicRecord.encoding[1] )
                result_dct['holdings_data'] = self.add_holdings_data( result )
            items.append( result_dct )
            pickle_dmp = pickle.dumps( items )
            log.debug( 'type(pickle_dmp), ```%s```' % type(pickle_dmp) )
            print pickle_dmp
            return pickle_dmp
        except Exception as e:
            self.close_connection()
            message = 'exception, ```%s```' % unicode(repr(e))
            # error_dict = self.make_error_dict()
            # log.error( 'in z3950_wrapper.Searcher.search(); error-info, `%s`' % pprint.pformat(error_dict) )
            log.error( message )

    # def search( self, key, value, marc_flag=False ):
    #     """ Convenience function.
    #         Called by utils.app_helper.HandlerHelper.query_josiah() """
    #     try:
    #         qstring = self.build_qstring( key, value )
    #         qobject = self.build_qobject( qstring )
    #         resultset = self.connection.search( qobject )
    #         items = []
    #         for result in resultset:
    #             item_dct = {}
    #             marc_record_object = Record( data=result.data.bibliographicRecord.encoding[1] )
    #             marc_dct = marc_record_object.as_dict()
    #             item_dct['marc_dct'] = marc_dct
    #             item_dct['holdings_data'] = self.add_holdings_data( result )
    #             items.append( item_dct )
    #         log.debug( 'items, ```%s```' % pprint.pformat(items) )
    #         jsn = json.dumps( items )
    #         print jsn
    #         return jsn
    #     except Exception as e:
    #         self.close_connection()
    #         error_dict = self.make_error_dict()
    #         self.logger.error( u'in z3950_wrapper.Searcher.search(); error-info, `%s`' % pprint.pformat(error_dict) )

    # def search( self, key, value, marc_flag=False ):
    #     """ Convenience function.
    #         Called by utils.app_helper.HandlerHelper.query_josiah() """
    #     try:
    #         qstring = self.build_qstring( key, value )
    #         qobject = self.build_qobject( qstring )
    #         resultset = self.connection.search( qobject )
    #         # return resultset
    #         # self.inspect_resultset( resultset )  # for debugging
    #         item_list = self.process_resultset( resultset, marc_flag )  # marc_flag typically False
    #         return item_list
    #     except Exception as e:
    #         self.close_connection()
    #         error_dict = self.make_error_dict()
    #         self.logger.error( u'in z3950_wrapper.Searcher.search(); error-info, `%s`' % pprint.pformat(error_dict) )

    def build_qstring( self, key, value ):
        """ Builds an arcane querystring, like `@attr 1=7 9780521593700`.
            Called by search() """
        if key == 'bib':
            key = 'id'
        dct = {
            'isbn': '@attr 1=7',
            'issn': '@attr 1=8',
            'id': '@attr 1=12',
            'oclc': '@attr 1=1007', }
        value = value   if key != 'oclc'   else self.update_oclc_value( value )
        qstring = '%s %s' % ( dct[key], value )
        log.debug( 'qstring, `%s`' % qstring )
        return qstring

    def update_oclc_value( self, value ):
        """ Updates oclc number to brown-formatted number if necessary.
            Reference: http://www.oclc.org/batchprocessing/controlnumber.htm
            Called by build_qstring() """
        if not ( value.startswith('ocn') or value.startswith(u'ocm') ):
            try:
                int_value = int(value)
                new_value = unicode(int_value).zfill( 8 )
                if int_value <= 99999999:
                    value = 'ocm%s' % new_value
                else:
                    value = 'ocn%s' % new_value
            except Exception as e:
                value = 'invalid_oclc_number'
        return value

    def build_qobject( self, qstring ):
        """ Builds and returns a PyZ3950.zoom.Query instance object.
            Called by search() """
        qobject = zoom.Query(
            'PQF'.encode('utf-8'),
            qstring.encode('utf-8')
            )
        log.debug( 'type(qobject), `%s`' % type(qobject) )
        log.debug( 'pprint.pformat(qobject), `%s`' % pprint.pformat(qobject) )
        return qobject

    def add_holdings_data( self, result ):
        """ Extracts holdings data if available.
            Called by process_resultset() """
        try:
            holdings_record_data = result.data.holdingsData
            log.debug( 'holdings_record_data, ```%s```' % holdings_record_data )
            holdings_data = self.process_holdings_data( holdings_record_data )
        except Exception as e:
            log.warning( 'error trying to read holdings data, ```{}```'.format(unicode(repr(e))) )
            holdings_data = []
        return holdings_data

    def close_connection( self ):
        """ Closes connection.
            Called by search() Exception. """
        log.debug( 'closing connection.')
        self.connection.close()

    ## end class Searcher()


def query_josiah( key, value, show_marc_param ):
    """ Perform actual query.
        Called by `if __name__ == '__main__':` """
    marc_flag = True if show_marc_param == 'true' else False
    srchr = Searcher(
        HOST=HOST, PORT=PORT, DB_NAME=DB_NAME, connect_flag=True
    )
    item_list = srchr.search( key, value, marc_flag )
    srchr.close_connection()
    return_dct = {
        'backend_response': item_list,
        'response_timestamp': unicode(datetime.datetime.now())
    }
    log.debug( 'return_dct, ```%s```' % pprint.pformat(return_dct) )
    # return return_dct
    return 'foo'


if __name__ == '__main__':
    log.debug( '\n\n---\nstarting main' )
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument(
        '--key', help='`isbn` or `oclc`'
    )
    parser.add_argument(
        '--value', help='the isbn or the oclc-number'
    )
    args = parser.parse_args()
    log.debug( 'args, ```%s```' % args )
    query_josiah( key=args.key, value=args.value, show_marc_param=False )


## Searcher() functions not currently used...

    # def inspect_resultset( self, resultset ):
    #     """ Logs wildly detailed info about resultset.
    #         Called by search() when debugging, developing. """
    #     log.debug( 'resultset, `%s`' % pprint.pformat(resultset) )
    #     log.debug( 'dir(resultset), `%s`' % pprint.pformat(dir(resultset)) )
    #     log.debug( 'resultset.__dict__, `%s`' % pprint.pformat(resultset.__dict__) )
    #     log.debug( 'len(resultset), `%s`' % pprint.pformat(len(resultset)) )
    #     log.debug( 'resultset[0], `%s`' % pprint.pformat(resultset[0]) )
    #     for (i, entry) in enumerate(resultset):
    #         log.debug( 'counter, `{}`'.format(i) )
    #         try:
    #             log.debug( 'type(entry), `{}`'.format(type(entry)) )
    #             log.debug( 'dir(entry), `%s`' % pprint.pformat(dir(entry)) )
    #             log.debug( 'entry.__dict__, `%s`' % pprint.pformat(entry.__dict__) )
    #             log.debug( 'entry.data, `%s`' % pprint.pformat(entry.data) )
    #             try:
    #                 ## bib info
    #                 log.debug( 'entry.data.bibliographicRecord, `%s`' % pprint.pformat(entry.data.bibliographicRecord) )
    #                 log.debug( 'entry.data.bibliographicRecord.encoding, `%s`' % pprint.pformat(entry.data.bibliographicRecord.encoding) )
    #                 record_instance = Record( data=entry.data.bibliographicRecord.encoding[1] )
    #                 log.debug( 'record_instance, `%s`' % pprint.pformat(record_instance) )
    #                 log.debug( 'dir(record_instance), `%s`' % pprint.pformat(dir(record_instance)) )
    #                 log.debug( 'record_instance.__dict__, `%s`' % pprint.pformat(record_instance.__dict__) )
    #                 log.debug( 'record_instance.as_dict(), `%s`' % pprint.pformat(record_instance.as_dict()) )
    #                 log.debug( 'record_instance.title(), `%s`' % pprint.pformat(record_instance.title()) )
    #             except:
    #                 log.debug( 'no `entry.data.bibliographicRecord`' )
    #             try:
    #                 ## holdings
    #                 log.debug( 'entry.data.holdingsData, `%s`' % pprint.pformat(entry.data.holdingsData) )
    #                 log.debug( 'entry.data.holdingsData[0], `%s`' % pprint.pformat(entry.data.holdingsData[0]) )
    #                 log.debug( 'entry.data.holdingsData[0][0], `%s`' % pprint.pformat(entry.data.holdingsData[0][0]) )
    #                 log.debug( 'entry.data.holdingsData[0][1].callNumber, `%s`' % pprint.pformat(entry.data.holdingsData[0][1].callNumber) )
    #             except:
    #                 log.debug( 'no `entry.data.holdingsData`' )
    #                 try:
    #                     record_instance_2 = Record( data=entry.data )
    #                     log.debug( 'record_instance_2.__dict__, ```{}```'.format(pprint.pformat(record_instance_2.__dict__)) )
    #                     log.debug( 'record_instance_2.as_dict(), ```{}```'.format(pprint.pformat(record_instance_2.as_dict())) )
    #                 except Exception as e:
    #                     log.debug( 'record_instance_2 instantiation exception, `{}`'.format(unicode(repr(e))) )
    #                 log.debug( 'type(record_instance_2), `{}`'.format(type(record_instance_2)) )
    #                 # log.debug( '' )
    #         except Exception as e:
    #             log.debug( 'inspection exception, `{}`'.format(unicode(repr(e))) )
    #     return

    # def process_resultset( self, resultset, marc_flag=False ):
    #     """ Iterates through resultset, extracting from marc-data and holdings-data.
    #         Called by search() """
    #     item_list = []
    #     for result in resultset:
    #         try:  ## start w/marc
    #             marc_record_object = Record( data=result.data.bibliographicRecord.encoding[1] )
    #         except Exception as e:
    #             log.warning( 'could not get a marc_record_object, Exception, {}'.format(unicode(repr(e))) )
    #             continue
    #         item_entry = self.process_marc_data( marc_record_object, marc_flag )
    #         item_entry['holdings_data'] = self.add_holdings_data( result )
    #         self.update_item_list( item_list, item_entry )
    #     log.debug( 'item_list, `%s`' % pprint.pformat(item_list) )
    #     return item_list

    # ## for process_resultset()... ##

    # def process_marc_data( self, marc_record_object, marc_flag ):
    #     """ Creates bib-dct.
    #         Called by process_resultset() """
    #     marc_dict = marc_record_object.as_dict()
    #     item_entry = {}
    #     if marc_flag:
    #         item_entry[u'raw_marc'] = marc_dict
    #     item_entry[u'title'] = marc_record_object.title()
    #     item_entry[u'callnumber'] = self.make_marc_callnumber( marc_dict )
    #     item_entry[u'items_data'] = self.make_items_data( marc_record_object )
    #     item_entry[u'isbn'] = marc_record_object.isbn()
    #     item_entry[u'lccn'] = self.make_lccn( marc_dict )
    #     item_entry[u'bibid'] = self.make_bibid( marc_dict )
    #     item_entry[u'issn'] = self.make_issn( marc_dict )
    #     item_entry[u'bib_url_josiah_classic'] = u'%s/record=%s' % ( u'https://josiah.brown.edu', item_entry[u'bibid'][1:-1] )  # removes period & check-digit
    #     item_entry[u'bib_url_josiah'] = 'https://search.library.brown.edu/catalog/{}/'.format( item_entry[u'bibid'][1:-1] )
    #     item_entry[u'oclc_brown'] = self.make_oclc_brown( marc_dict )
    #     log.debug( 'pprint.pformat(item_entry), `%s`' % pprint.pformat(item_entry) )
    #     return item_entry

    # def update_item_list( self, item_list, item_entry ):
    #     """ Adds item if it's not a duplicate.
    #         Called by process_resultset() """
    #     if item_list == []:
    #         item_list.append( item_entry )
    #     else:
    #         add_flag = True
    #         for existing_entry in item_list:
    #             existing_bib = existing_entry['bibid']
    #             if item_entry['bibid'] == existing_bib:
    #                 add_flag = False
    #                 break
    #         if add_flag == True:
    #             item_list.append( item_entry )
    #     return item_list

    # ## ...end for process_resultset() ##

    # def process_holdings_data( self, holdings_data ):
    #     """ Pulls out callnumber, location, and public_note.
    #         Called by add_holdings_data() """
    #     record_holdings_data = []
    #     for holdings_entry in holdings_data:
    #         entry = {}
    #         holdings_object = holdings_entry[1]
    #         entry[u'callNumber'] = holdings_object.callNumber
    #         entry[u'localLocation'] = holdings_object.localLocation
    #         entry[u'publicNote'] = holdings_object.publicNote
    #         record_holdings_data.append( entry )
    #     log.debug( 'pprint.pformat(record_holdings_data), `%s`' % pprint.pformat(record_holdings_data) )
    #     return record_holdings_data

    # ## for process_marc_data()... ##

    # def make_marc_callnumber( self, marc_dict ):
    #     """ Populates callnumber value.
    #         Called by process_marc_data() """
    #     ( callnumber, subfield_callnumber ) = ( u'callnumber_not_available', u'' )
    #     for field in marc_dict[u'fields']:
    #         ( key, val ) = field.items()[0]
    #         if key == u'050' or key == u'090':
    #             for subfield in field[key][u'subfields']:
    #                 ( key2, val2 ) = subfield.items()[0]
    #                 subfield_callnumber = u'%s %s' % (subfield_callnumber, val2)
    #             callnumber = subfield_callnumber.strip()
    #             break
    #     log.debug( 'callnumber, `%s`' % callnumber )
    #     return callnumber

    # def make_items_data( self, marc_record_object ):
    #     """ Processes each item's 945 field for:
    #           barcode, callnumber, item_id, itype, location, & status
    #         Called by process_marc_data() """
    #     items = marc_record_object.get_fields(u'945') or []
    #     return_items_data = []
    #     for item in items:
    #         items_dict = dict(
    #             barcode=self.make_945_barcode( item  ),
    #             item_id=item[u'y'].lstrip(u'.'),
    #             location=item[u'l'].strip(),
    #             callnumber=item[u'c'],  #This seems to be the second half of the callnumber only
    #             status=item[u's'].strip(),
    #             itype=item[u't'].strip()
    #             )
    #         return_items_data.append( self.interpret_itemsdict(items_dict, marc_record_object) )
    #     # log.debug( u'in z3950_wrapper.Searcher.make_items_data(); return_items_data, `%s`' % return_items_data )
    #     log.debug( 'return_items_data, ```{}```'.format(pprint.pformat(return_items_data)) )
    #     return return_items_data

    # def make_945_barcode( self, item ):
    #     """ Populates barcode value.
    #         Called by make_items_data() """
    #     barcode = item[u'i']
    #     if barcode is not None:
    #         barcode = barcode.replace(u' ', u'')
    #     return barcode

    # def interpret_itemsdict( self, dct, marc_record_object ):
    #     """ Stubs data to produce.
    #         Called by make_items_data() """
    #     dct[u'location_interpreted'] = u'coming'
    #     dct[u'status_interpreted'] = u'coming'
    #     dct[u'itype_interpreted'] = u'coming'
    #     dct[u'callnumber_interpreted'] = self.build_full_callnumber( dct[u'callnumber'], marc_record_object.get_fields(u'090') or [] )
    #     return dct

    # def build_full_callnumber( self, callnumber_suffix, nine_oh_obj ):
    #     """ Adds interpreted full callnumber for possible need to match on holdings data.
    #         Called by interpret_itemsdict() """
    #     log.debug( 'callnumber_suffix, `%s`' % callnumber_suffix )
    #     log.debug( 'nine_oh_obj, `%s`' % nine_oh_obj )
    #     full_callnumber = u''
    #     if nine_oh_obj:
    #         full_callnumber = u'%s %s %s' % ( nine_oh_obj[0][u'a'], nine_oh_obj[0][u'b'], callnumber_suffix )
    #     return full_callnumber

    # def make_lccn( self, marc_dict ):
    #     """ Populates lccn value.
    #         Called by process_marc_data() """
    #     lccn = u'lccn_not_available'
    #     for field in marc_dict[u'fields']:
    #         ( key, val ) = field.items()[0]
    #         if key == u'010':
    #             for subfield in field[key][u'subfields']:
    #                 ( key2, val2 ) = subfield.items()[0]
    #                 if key2 == u'a':
    #                     lccn = val2
    #                     break
    #     log.debug( 'lccn, `%s`' % lccn )
    #     return lccn

    # def make_bibid( self, marc_dict ):
    #     bibid = u'bibid_not_available'
    #     for field in marc_dict[u'fields']:
    #         ( key, val ) = field.items()[0]
    #         if key == u'907':
    #             for subfield in field[key][u'subfields']:
    #                 ( key2, val2 ) = subfield.items()[0]
    #                 if key2 == u'a':
    #                     bibid = val2
    #                     break
    #     log.debug( 'bibid, `%s`' % bibid )
    #     return bibid

    # def make_issn( self, marc_dict, issn=u'issn_not_available' ):
    #     for field in marc_dict[u'fields']:
    #         ( key, val ) = field.items()[0]
    #         if key == u'022':
    #             for subfield in field[key][u'subfields']:
    #                 ( key2, val2 ) = subfield.items()[0]
    #                 if key2 == u'a':
    #                     issn = val2
    #                 elif key2 == u'l' and issn == u'issn_not_available':
    #                     issn = val2
    #     log.debug( 'bibid, `%s`' % issn )
    #     return issn

    # def make_oclc_brown( self, marc_dict ):
    #     oclc = u'oclc_not_available'
    #     for field in marc_dict[u'fields']:
    #         ( key, val ) = field.items()[0]
    #         if key == u'001':
    #             oclc = val
    #             break
    #     log.debug( 'oclc, `%s`' % oclc )
    #     return oclc

    # ## ...end for process_marc_data() ##

    # def make_error_dict( self ):
    #     """ Handles high-level search exception.
    #         Called by search() """
    #     error_dict = {
    #         u'error-type': sys.exc_info()[0],
    #         u'error-message': sys.exc_info()[1],
    #         u'line-number': sys.exc_info()[2].tb_lineno
    #         }
    #     return error_dict
