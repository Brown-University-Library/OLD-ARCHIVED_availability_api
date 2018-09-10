# -*- coding: utf-8 -*-

"""
For log analysis.
"""

import datetime, glob, json, logging, os, pprint, sys

## configure django environment
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
cwd = os.getcwd()  # this assumes the cron call has cd-ed into the project directory
if cwd not in sys.path:
    sys.path.append( cwd )
django.setup()

## continue normal imports
from log_parser import LogParser
from availability_app.models import Tracker


logging.basicConfig(
    filename=os.environ['AVL_API__LOG_PATH'],
    level=logging.DEBUG,
    format='[%(asctime)s] %(levelname)s [%(module)s-%(funcName)s()::%(lineno)d] %(message)s',
    datefmt='%d/%b/%Y %H:%M:%S',
    )
log = logging.getLogger(__name__)

parser = LogParser()


class LogAnalyzer( object ):
    """ Analyzes logs and populates db. """

    def __init__( self ):
        self.last_checked_path = os.environ['AVL_API__LAST_CHECKED_PATH']
        self.log_dir_path = os.path.dirname( os.environ['AVL_API__LOG_PATH'] )

    def check_logs( self ):
        """ Checks recent logs.
            Called by: ```if __name__ == '__main__'```; triggered via cronjob """
        last_check_date = self.get_last_check_date()
        worthy_entries = self.scan_log_files( last_check_date )
        for entry in worthy_entries:
            # log_parts_dct = parser.make_parts( entry )
            entry_datetime = parser.get_date( log_parts_dct['date_string'] )
            data_dct = json.loads( log_parts_dct['json_string'] )
            self.process_entry( entry_datetime, data_dct )
        return

    def get_last_check_date( self ):
        """ Returns date of last-log-entry checked.
            Called by check_logs() """
        with open( self.last_checked_path ) as fh:
            dt_str_1 = json.loads( fh.read() )
            dt_str_2 = dt_str_1[0:26]  # in case 'Z' or '+' time-zone stuff is appended
            dt= datetime.datetime.strptime( dt_str_2, '%Y-%m-%dT%H:%M:%S.%f' )
            log.debug( 'dt, `%s`' % dt )
            return dt

    def scan_log_files( self, last_check_date ):
        """ Returns list of log-entry dcts to process (since last_check_date).
            Called by check_logs() """
        worthy_data_dct_entries = []
        # log_file_list = sorted( glob.glob('%s/availability_api_stats*' % self.log_dir_path) )
        # log_file_list = sorted( glob.glob('%s/*.log' % self.log_dir_path) )
        glob_path_string = '%s/availability_api_stats*' % self.log_dir_path
        log.debug( 'glob_path_string, ```%s```' % glob_path_string )
        log_file_list = sorted( glob.glob(glob_path_string) )
        log.debug( 'log_file_list, ```%s```' % log_file_list )
        for file_path in log_file_list:
            with open( file_path ) as fh:
                for line in fh.readlines():
                    log_line_parts_dct = parser.make_parts( line )
                    log.debug( 'log_line_parts_dct, ```%s```' % log_line_parts_dct )
                    entry_datetime = parser.get_date( log_line_parts_dct['date_string'] )
                    log.debug( 'entry_datetime, ```%s```' % entry_datetime )
        log.debug( 'worthy_data_dct_entries, ```%s```' % worthy_data_dct_entries )
        return worthy_data_dct_entries


    def process_entry( self, entry_datetime, data_dct ):
        """ Updates db with data.
            Called by check_logs() """
        log_date = entry_datetime.date()
        try:
            rcrd = Tracker.objects.get( count_date=dtm_obj.date() )
        except:
            rcrd = Tracker()
        ## if 'ip' is 'x' and 'oclc' in 'query_url': rcrd.oclc += 1 --> rcrd.save()
        pass

    ## end LogAnalyzer()


if __name__ == '__main__':
    log.debug( '\n---\nstarting' )
    analyzer = LogAnalyzer()
    analyzer.check_logs()
