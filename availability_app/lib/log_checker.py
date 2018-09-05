# -*- coding: utf-8 -*-

"""
For log analysis.
"""

import datetime, json, logging, os, pprint


log = logging.getLogger(__name__)


class LogAnalyzer( object ):
    """ Analyzes logs and populates db. """

    def __init__( self ):
        self.last_checked_path = os.environ['AVL_API__LAST_CHECKED_PATH']

    def check_logs( self ):
        """ Checks recent logs.
            Called by: ```if __name__ == '__main__'```; triggered via cronjob """
        return

    ## end LogAnalyzer()


if __name__ == '__main__':
    analyzer = LogAnalyzer()
    analyzer.check_logs()
