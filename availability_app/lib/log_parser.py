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
        pass

    # def make_parts( self, line ):
    #     """ Splits line into date-part and json-data-part.
    #         Called by: TBD """
    #     parts_dct = { 'date_string': '', 'json_string': '' }
    #     parts = line.split()
    #     parts_dct['date_string'] = parts[0] + ' ' + parts[1]
    #     j_parts = parts[4:]
    #     parts_dct['json_string'] = ' '.join( j_parts )
    #     log.debug( 'parts_dct, ```%s```' % pprint.pformat(parts_dct) )
    #     return parts_dct

    def get_date( self, date_string ):
        """ Returns date-object.
            Called by: TBD """
        dt = datetime.datetime.strptime( date_string, '[%d/%b/%Y %H:%M:%S]' )
        return dt

    def get_date( self, date_string ):
        """ Returns date-object.
            Called by: TBD """
        dt_str_1 = date_string[0:26]  # in case 'Z' or '+' time-zone stuff is appended
        dt = datetime.datetime.strptime( dt_str_1, '%Y-%m-%dT%H:%M:%S.%f' )
        log.debug( 'dt, `%s`' % str(dt) )
        return dt


    # def get_json( self, json_string ):
    #     """ Returns date-object.
    #         Function only called by test, to validate the json. """
    #     dct = json.loads( json_string )
    #     return dct


    ## end LogParser()
