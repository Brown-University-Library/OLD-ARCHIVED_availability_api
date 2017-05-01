# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import logging


log = logging.getLogger(__name__)


class Interpreter( object ):
    """ Contains functions for interpreting parsed z39.50 data. """

    def __init__( self ):
        self.HIDE_BUTTON_STATUSES
        self.HIDE_BUTTON_LOCATIONS
        self.ALTERNATE_LOCATIONS
