# -*- coding: utf-8 -*-

"""
Parser for custom log.
"""

import datetime, json, logging, os, pickle, pprint, subprocess, urllib
from availability_app import settings_app


log = logging.getLogger(__name__)


class LogParser( object ):
    """ Custom log parser. """

    def __init__( self ):
        self.EAN13 = None  # validated-canonical 13-digit isbn

    def get_date( self, date_string ):
        """ Returns date-object.
            Called by: LogAnalyzer.process_entry() and LogAnalyzer.update_trckr() """
        dt_str_1 = date_string[0:26]  # in case 'Z' or '+' time-zone stuff is appended
        dt = datetime.datetime.strptime( dt_str_1, '%Y-%m-%dT%H:%M:%S.%f' )
        log.debug( 'dt, `%s`' % str(dt) )
        return dt

    ## end LogParser()
