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

    ## end LogParser()
