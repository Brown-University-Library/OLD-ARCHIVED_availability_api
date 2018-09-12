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

os.nice( 19 )


class LogAnalyzer( object ):
    """ Analyzes logs and populates db. """

    def __init__( self ):
        self.last_checked_json_path = os.environ['AVL_API__LAST_CHECKED_JSON_PATH']
        self.log_dir_path = os.path.dirname( os.environ['AVL_API__LOG_PATH'] )
        self.last_read_log_datetime = None
        self.legit_ips = json.loads( os.environ['AVL_API__LEGIT_IPS_JSON'] )
        self.legit_user_agents = json.loads( os.environ['AVL_API__LEGIT_USER_AGENTS_JSON'] )

    def check_logs( self ):
        """ Checks recent logs.
            Called by: ```if __name__ == '__main__'```; triggered via cronjob """
        self.get_last_read_log_datetime()
        worthy_entries = self.scan_log_files()
        for entry_data_dct in worthy_entries:
            self.process_entry( entry_data_dct )
        return

    def get_last_read_log_datetime( self ):
        """ Returns datetime of saved last-log-entry json.
            Called by check_logs() """
        with open( self.last_checked_json_path ) as fh:
            dt_str_1 = json.loads( fh.read() )
            dt_str_2 = dt_str_1[0:26]  # in case 'Z' or '+' time-zone stuff is appended
            self.last_read_log_datetime = datetime.datetime.strptime( dt_str_2, '%Y-%m-%dT%H:%M:%S.%f' )
            log.debug( 'self.last_read_log_datetime, `%s`' % self.last_read_log_datetime )
            return

    def scan_log_files( self ):
        """ Returns list of log-entry dcts to process (since last_check_date).
            Called by check_logs() """
        worthy_data_dct_entries = []
        # log_file_list = sorted( glob.glob('%s/availability_api_stats*' % self.log_dir_path) )
        # log_file_list = sorted( glob.glob('%s/*.log' % self.log_dir_path) )
        glob_path_string = '%s/stats.log*' % self.log_dir_path
        log.debug( 'glob_path_string, ```%s```' % glob_path_string )
        log_file_list = sorted( glob.glob(glob_path_string) )
        log.debug( 'log_file_list, ```%s```' % log_file_list )
        for file_path in log_file_list:
            with open( file_path ) as fh:
                for line in fh.readlines():
                    data_dct = None
                    try:
                        data_dct = json.loads( line )
                    except Exception as e:
                        log.warning( 'could not read as json the line, ```%s```' % line )
                        pass
                    if data_dct:
                        log.debug( 'data_dct, ```%s```' % data_dct )
                        entry_datetime = parser.get_date( data_dct['datetime'] )
                        log.debug( 'entry_datetime, ```%s```' % entry_datetime )
                        if entry_datetime > self.last_read_log_datetime:
                            worthy_data_dct_entries.append( data_dct )
        log.debug( 'worthy_data_dct_entries, ```%s```' % pprint.pformat(worthy_data_dct_entries) )
        return worthy_data_dct_entries

    def process_entry( self, data_dct ):
        """ Updates db with data.
            Called by check_logs() """
        entry_datetime_obj = parser.get_date( data_dct['datetime'] )
        entry_date_obj = entry_datetime_obj.date()
        try:
            log.debug( 'date_record will be updated' )
            trckr = Tracker.objects.get( count_date=entry_date_obj )
        except:
            log.debug( 'new date-record will be created' )
            trckr = Tracker()
            trckr.count_date = entry_date_obj
        self.update_trckr( trckr, data_dct )
        ## if 'ip' is 'x' and 'oclc' in 'query_url': rcrd.oclc += 1 --> rcrd.save()
        return

    def update_trckr( self, trckr, data_dct ):
        """ Updates tracker entry and saves last-log-entry-checked.
            Called by process_entry() """
        legit = False
        if data_dct['ip'] in self.legit_ips and data_dct['user_agent'] in self.legit_user_agents:
            legit = True
        if legit:
            if '/v1/isbn/' in data_dct['query']:
                trckr.ezb_isbn_count += 1
            elif '/v1/oclc/' in data_dct['query']:
                trckr.ezb_oclc_count += 1
        else:
            trckr.unofficial_access_count += 1
        self.update_last_read_log_datetime_json( parser.get_date(data_dct['datetime']) )
        trckr.save()
        return

    def update_last_read_log_datetime_json( self, datetime_obj ):
        """ Updates saved json datetime string.
            Called by: update_trckr() """
        with open( self.last_checked_json_path, 'w' ) as fh:
            datetime_str = json.dumps( datetime_obj.isoformat() )
            fh.write( datetime_str )
            log.debug( 'datetime_str, ```%s``` saved' % datetime_str )
        return

    ## end LogAnalyzer()


if __name__ == '__main__':
    log.debug( '\n---\nstarting' )
    analyzer = LogAnalyzer()
    analyzer.check_logs()
