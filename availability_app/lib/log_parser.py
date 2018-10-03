# -*- coding: utf-8 -*-

"""
Parser for custom log.
"""

import datetime, json, logging, os, pickle, pprint, subprocess, urllib
import isbnlib
from availability_app import settings_app


log = logging.getLogger(__name__)


class LogParser( object ):
    """ Custom log parser. """

    def __init__( self ):
        pass

    def get_date( self, date_string ):
        """ Returns date-object.
            Called by: LogAnalyzer.process_entry() and LogAnalyzer.update_trckr() """
        dt_str_1 = date_string[0:26]  # in case 'Z' or '+' time-zone stuff is appended
        dt = datetime.datetime.strptime( dt_str_1, '%Y-%m-%dT%H:%M:%S.%f' )
        log.debug( 'dt, `%s`' % str(dt) )
        return dt

    def validate_isbn( self, isbn ):
        """ Returns boolean.
            Called by TBD """
        if isbnlib.is_isbn10(isbn) or isbnlib.is_isbn13(isbn):
            rslt = True
        else:
            rslt = False
            log.debug( 'isbn, `%s` is not valid' )
        return rslt

    ## end LogParser()
