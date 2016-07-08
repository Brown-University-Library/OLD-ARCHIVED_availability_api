# -*- coding: utf-8 -*-

from __future__ import unicode_literals

"""
Wrapper for z3950 library call & data-extraction.
Resources:
- z3950 library docs, http://www.panix.com/~asl2/software/PyZ3950/zoom.html
- list of record formats,  http://lists.indexdata.dk/pipermail/zoom/2003-November/000547.html
"""

import logging, os, pprint, sys

from PyZ3950 import zoom  # fork, git+https://github.com/Brown-University-Library/PyZ3950.git
from pymarc import Record  # pymarc==3.0.2


log = logging.getLogger(__name__)


class Searcher( object ):

    def __init__( self, HOST, PORT, DB_NAME, connect_flag=False ):
        self.HOST = HOST   if type(HOST) == unicode   else HOST.decode(u'utf-8')
        self.PORT = PORT   if type(PORT) == unicode   else PORT.decode(u'utf-8')
        self.DB_NAME = DB_NAME   if type(DB_NAME) == unicode   else DB_NAME.decode(u'utf-8')
        self.logger = log
        self.connection = self.connect()   if connect_flag   else None  # allows Searcher to be instantiated w/o connecting

    def connect( self ):
        """ Connects to z3950 server.
            Called by __init__() """
        conn = zoom.Connection(
            self.HOST,
            int(self.PORT),
            databaseName=self.DB_NAME,
            preferredRecordSyntax=u'OPAC',  # Getting records in "opac" format. (Others were not more helpful.)
            charset=u'utf-8' )
        self.logger.debug( u'in z3950_wrapper.Searcher.connect(); connection made.')
        return conn

    def close_connection( self ):
        """ Closes connection.
            Called by search() Exception. """
        self.logger.debug( u'in z3950_wrapper.Searcher.close_connection(); closing connection.')
        self.connection.close()

    def search( self, key, value, marc_flag=False ):
        """ Convenience function.
            Called by utils.app_helper.HandlerHelper.query_josiah() """
        try:
            qstring = self.build_qstring( key, value )
            qobject = self.build_qobject( qstring )
            resultset = self.connection.search( qobject )
            self.inspect_resultset( resultset )
            item_list = self.process_resultset( resultset, marc_flag )  # marc_flag typically False
            return item_list
        except Exception as e:
            self.close_connection()
            error_dict = self.make_error_dict()
            self.logger.error( u'in z3950_wrapper.Searcher.search(); error-info, `%s`' % pprint.pformat(error_dict) )

    def build_qstring( self, key, value ):
        """ Builds an arcane querystring, like `@attr 1=7 9780521593700`.
            Called by search() """
        if key == u'bib':
            key = u'id'
        dct = {
            u'isbn': u'@attr 1=7',
            u'issn': u'@attr 1=8',
            u'id': u'@attr 1=12',
            u'oclc': u'@attr 1=1007', }
        value = value   if key != u'oclc'   else self.update_oclc_value( value )
        qstring = u'%s %s' % ( dct[key], value )
        self.logger.debug( u'in z3950_wrapper.Searcher.build_qstring(); qstring, `%s`' % qstring )
        return qstring

    def update_oclc_value( self, value ):
        """ Updates oclc number to brown-formatted number if necessary.
            Reference: http://www.oclc.org/batchprocessing/controlnumber.htm
            Called by build_qstring() """
        if not ( value.startswith(u'ocn') or value.startswith(u'ocm') ):
            try:
                int_value = int(value)
                new_value = unicode(int_value).zfill( 8 )
                if int_value <= 99999999:
                    value = u'ocm%s' % new_value
                else:
                    value = u'ocn%s' % new_value
            except Exception, e:
                value = u'invalid_oclc_number'
        return value

    def build_qobject( self, qstring ):
        """ Builds and returns a PyZ3950.zoom.Query instance object.
            Called by search() """
        qobject = zoom.Query(
            u'PQF'.encode(u'utf-8'),
            qstring.encode(u'utf-8')
            )
        self.logger.debug( u'in z3950_wrapper.Searcher.build_qobject(); type(qobject), `%s`' % type(qobject) )
        self.logger.debug( u'in z3950_wrapper.Searcher.build_qobject(); pprint.pformat(qobject), `%s`' % pprint.pformat(qobject) )
        return qobject

    def inspect_resultset( self, resultset ):
        """ Logs wildly detailed info about resultset.
            Called by search() when debugging, developing. """
        self.logger.debug( 'resultset, `%s`' % pprint.pformat(resultset) )
        self.logger.debug( 'dir(resultset), `%s`' % pprint.pformat(dir(resultset)) )
        self.logger.debug( 'resultset.__dict__, `%s`' % pprint.pformat(resultset.__dict__) )
        self.logger.debug( 'len(resultset), `%s`' % pprint.pformat(len(resultset)) )
        self.logger.debug( 'resultset[0], `%s`' % pprint.pformat(resultset[0]) )
        for (i, entry) in enumerate(resultset):
            log.debug( 'counter, `{}`'.format(i) )
            try:
                log.debug( 'type(entry), `{}`'.format(type(entry)) )
                self.logger.debug( 'dir(entry), `%s`' % pprint.pformat(dir(entry)) )
                self.logger.debug( 'entry.__dict__, `%s`' % pprint.pformat(entry.__dict__) )
                self.logger.debug( 'entry.data, `%s`' % pprint.pformat(entry.data) )
                try:
                    ## bib info
                    self.logger.debug( 'entry.data.bibliographicRecord, `%s`' % pprint.pformat(entry.data.bibliographicRecord) )
                    self.logger.debug( 'entry.data.bibliographicRecord.encoding, `%s`' % pprint.pformat(entry.data.bibliographicRecord.encoding) )
                    record_instance = Record( data=entry.data.bibliographicRecord.encoding[1] )
                    self.logger.debug( 'record_instance, `%s`' % pprint.pformat(record_instance) )
                    self.logger.debug( 'dir(record_instance), `%s`' % pprint.pformat(dir(record_instance)) )
                    self.logger.debug( 'record_instance.__dict__, `%s`' % pprint.pformat(record_instance.__dict__) )
                    self.logger.debug( 'record_instance.as_dict(), `%s`' % pprint.pformat(record_instance.as_dict()) )
                    self.logger.debug( 'record_instance.title(), `%s`' % pprint.pformat(record_instance.title()) )
                except:
                    log.debug( 'no `entry.data.bibliographicRecord`' )
                try:
                    ## holdings
                    self.logger.debug( 'entry.data.holdingsData, `%s`' % pprint.pformat(entry.data.holdingsData) )
                    self.logger.debug( 'entry.data.holdingsData[0], `%s`' % pprint.pformat(entry.data.holdingsData[0]) )
                    self.logger.debug( 'entry.data.holdingsData[0][0], `%s`' % pprint.pformat(entry.data.holdingsData[0][0]) )
                    self.logger.debug( 'entry.data.holdingsData[0][1].callNumber, `%s`' % pprint.pformat(entry.data.holdingsData[0][1].callNumber) )
                except:
                    log.debug( 'no `entry.data.holdingsData`' )
                    try:
                        record_instance_2 = Record( data=entry.data )
                        log.debug( 'record_instance_2.__dict__, ```{}```'.format(pprint.pformat(record_instance_2.__dict__)) )
                        log.debug( 'record_instance_2.as_dict(), ```{}```'.format(pprint.pformat(record_instance_2.as_dict())) )
                    except Exception as e:
                        log.debug( 'record_instance_2 instantiation exception, `{}`'.format(unicode(repr(e))) )
                    log.debug( 'type(record_instance_2), `{}`'.format(type(record_instance_2)) )
                    # log.debug( '' )
            except Exception as e:
                log.debug( 'inspection exception, `{}`'.format(unicode(repr(e))) )
        return

    def process_resultset( self, resultset, marc_flag=False ):
        """ Iterates through resultset, extracting from marc-data and holdings-data.
            Called by search() """
        item_list = []
        for result in resultset:
            ## start w/marc
            log.debug( 'type(result), `{}`'.format(type(result)) )
            log.debug( 'result, `{}`'.format(repr(result)) )
            log.debug( 'result.data, ```{}```'.format(pprint.pformat(result.data)) )
            try:
                marc_record_object = Record( data=result.data.bibliographicRecord.encoding[1] )
                log.debug( 'marc_record_object obtained' )
            except Exception as e:
                log.warning( 'could not get a marc_record_object, Exception, {}'.format(unicode(repr(e))) )
            item_entry = self.process_marc_data( marc_record_object, marc_flag )
            ## add holdings
            holdings_record_data = result.data.holdingsData
            item_entry[u'holdings_data'] = self.process_holdings_data( holdings_record_data )
            item_list.append( item_entry )
        self.logger.debug( u'in z3950_wrapper.Searcher.process_resultset, pprint.pformat(item_list), `%s`' % pprint.pformat(item_list) )
        return item_list

    def process_holdings_data( self, holdings_data ):
        """ Pulls out callnumber, location, and public_note.
            Called by process_resultset() """
        record_holdings_data = []
        for holdings_entry in holdings_data:
            entry = {}
            holdings_object = holdings_entry[1]
            entry[u'callNumber'] = holdings_object.callNumber
            entry[u'localLocation'] = holdings_object.localLocation
            entry[u'publicNote'] = holdings_object.publicNote
            record_holdings_data.append( entry )
        self.logger.debug( u'in z3950_wrapper.Searcher.process_holdings_data, pprint.pformat(record_holdings_data), `%s`' % pprint.pformat(record_holdings_data) )
        return record_holdings_data

    def process_marc_data( self, marc_record_object, marc_flag ):
        """ Hmnn....
            Called by process_resultset() """
        marc_dict = marc_record_object.as_dict()
        item_entry = {}
        if marc_flag:
            item_entry[u'raw_marc'] = marc_dict
        item_entry[u'title'] = marc_record_object.title()
        item_entry[u'callnumber'] = self.make_marc_callnumber( marc_dict )
        item_entry[u'items_data'] = self.make_items_data( marc_record_object )
        item_entry[u'isbn'] = marc_record_object.isbn()
        item_entry[u'lccn'] = self.make_lccn( marc_dict )
        item_entry[u'bibid'] = self.make_bibid( marc_dict )
        item_entry[u'issn'] = self.make_issn( marc_dict )
        item_entry[u'josiah_bib_url'] = u'%s/record=%s' % ( u'https://josiah.brown.edu', item_entry[u'bibid'][1:-1] )  # removes period & check-digit
        item_entry[u'oclc_brown'] = self.make_oclc_brown( marc_dict )
        self.logger.debug( u'in z3950_wrapper.Searcher.process_marc_data(); pprint.pformat(item_entry), `%s`' % pprint.pformat(item_entry) )
        return item_entry

    def make_marc_callnumber( self, marc_dict ):
        ( callnumber, subfield_callnumber ) = ( u'callnumber_not_available', u'' )
        for field in marc_dict[u'fields']:
            ( key, val ) = field.items()[0]
            if key == u'050' or key == u'090':
                for subfield in field[key][u'subfields']:
                    ( key2, val2 ) = subfield.items()[0]
                    subfield_callnumber = u'%s %s' % (subfield_callnumber, val2)
                callnumber = subfield_callnumber.strip()
                break
        self.logger.debug( u'in z3950_wrapper.Searcher.make_marc_callnumber(); callnumber, `%s`' % callnumber )
        return callnumber

    def make_items_data( self, marc_record_object ):
        """ Processes each item's 945 field for:
              barcode, callnumber, item_id, itype, location, & status """
        items = marc_record_object.get_fields(u'945') or []
        return_items_data = []
        for item in items:
            items_dict = dict(
                barcode=self.make_945_barcode( item  ),
                item_id=item[u'y'].lstrip(u'.'),
                location=item[u'l'].strip(),
                callnumber=item[u'c'],  #This seems to be the second half of the callnumber only
                status=item[u's'].strip(),
                itype=item[u't'].strip()
                )
            return_items_data.append( self.interpret_itemsdict(items_dict, marc_record_object) )
        # self.logger.debug( u'in z3950_wrapper.Searcher.make_items_data(); return_items_data, `%s`' % return_items_data )
        log.debug( u'in z3950_wrapper.Searcher.make_items_data(); return_items_data, ```{}```'.format(pprint.pformat(return_items_data)) )
        return return_items_data

    def make_945_barcode( self, item ):
        barcode = item[u'i']
        if barcode is not None:
            barcode = barcode.replace(u' ', u'')
        return barcode

    def interpret_itemsdict( self, dct, marc_record_object ):
        dct[u'location_interpreted'] = u'coming'
        dct[u'status_interpreted'] = u'coming'
        dct[u'itype_interpreted'] = u'coming'
        dct[u'callnumber_interpreted'] = self.build_full_callnumber( dct[u'callnumber'], marc_record_object.get_fields(u'090') or [] )
        return dct

    def build_full_callnumber( self, callnumber_suffix, nine_oh_obj ):
        """ Adds interpreted full callnumber for possible need to match on holdings data. """
        self.logger.debug( u'in z3950_wrapper.Searcher.build_full_callnumber(); callnumber_suffix, `%s`' % callnumber_suffix )
        self.logger.debug( u'in z3950_wrapper.Searcher.build_full_callnumber(); nine_oh_obj, `%s`' % nine_oh_obj )
        full_callnumber = u''
        if nine_oh_obj:
            full_callnumber = u'%s %s %s' % ( nine_oh_obj[0][u'a'], nine_oh_obj[0][u'b'], callnumber_suffix )
        return full_callnumber

    def make_lccn( self, marc_dict ):
        lccn = u'lccn_not_available'
        for field in marc_dict[u'fields']:
            ( key, val ) = field.items()[0]
            if key == u'010':
                for subfield in field[key][u'subfields']:
                    ( key2, val2 ) = subfield.items()[0]
                    if key2 == u'a':
                        lccn = val2
                        break
        self.logger.debug( u'in z3950_wrapper.Searcher.make_lccn(); lccn, `%s`' % lccn )
        return lccn

    def make_bibid( self, marc_dict ):
        bibid = u'bibid_not_available'
        for field in marc_dict[u'fields']:
            ( key, val ) = field.items()[0]
            if key == u'907':
                for subfield in field[key][u'subfields']:
                    ( key2, val2 ) = subfield.items()[0]
                    if key2 == u'a':
                        bibid = val2
                        break
        self.logger.debug( u'in z3950_wrapper.Searcher.make_bibid(); bibid, `%s`' % bibid )
        return bibid

    def make_issn( self, marc_dict, issn=u'issn_not_available' ):
        for field in marc_dict[u'fields']:
            ( key, val ) = field.items()[0]
            if key == u'022':
                for subfield in field[key][u'subfields']:
                    ( key2, val2 ) = subfield.items()[0]
                    if key2 == u'a':
                        issn = val2
                    elif key2 == u'l' and issn == u'issn_not_available':
                        issn = val2
        self.logger.debug( u'in z3950_wrapper.Searcher.make_bibid(); bibid, `%s`' % issn )
        return issn

    def make_oclc_brown( self, marc_dict ):
        oclc = u'oclc_not_available'
        for field in marc_dict[u'fields']:
            ( key, val ) = field.items()[0]
            if key == u'001':
                oclc = val
                break
        self.logger.debug( u'in z3950_wrapper.Searcher.make_oclc_brown(); oclc, `%s`' % oclc )
        return oclc

    def make_error_dict( self ):
        error_dict = {
            u'error-type': sys.exc_info()[0],
            u'error-message': sys.exc_info()[1],
            u'line-number': sys.exc_info()[2].tb_lineno
            }
        return error_dict

    # end class Searcher()
