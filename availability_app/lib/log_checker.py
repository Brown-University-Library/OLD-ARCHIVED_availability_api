# -*- coding: utf-8 -*-

"""
For log analysis.
"""

import datetime, json, logging, os, pprint
from log_parser import LogParser
from availability_app.models import Tracker


log = logging.getLogger(__name__)
parser = LogParser()


class LogAnalyzer( object ):
    """ Analyzes logs and populates db. """

    def __init__( self ):
        self.last_checked_path = os.environ['AVL_API__LAST_CHECKED_PATH']

    def check_logs( self ):
        """ Checks recent logs.
            Called by: ```if __name__ == '__main__'```; triggered via cronjob """
        last_check_date = self.get_last_check_date()
        worthy_entries = self.check_files( last_check_date )
        for entry in worthy_entries:
            log_parts_dct = parser.make_parts( entry )
            entry_datetime = parser.get_date( log_parts_dct['date_string'] )
            data_dct = json.loads( log_parts_dct['json_string'] )
            self.process_entry( entry_datetime, data_dct )
        return

    def process_entry( self, entry_datetime, data_dct ):
        """ Updates db with data.
            Called by check_logs() """
        log_date = entry_datetime.date()
        try:
            rcrd = Tracker.objects.get( count_date=dtm_obj.date() )
        except:
            rcrd = Tracker()
        pass

    ## end LogAnalyzer()


if __name__ == '__main__':
    analyzer = LogAnalyzer()
    analyzer.check_logs()
