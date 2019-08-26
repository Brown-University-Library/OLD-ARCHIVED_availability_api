"""
Helper for views.v2_bib()
"""

import datetime, logging, os, pprint

# from availability_app import settings_app


log = logging.getLogger(__name__)


class BibInfo:

    def build_query_dct( self, request, rq_now ):
        """ Builds query-dct part of response.
            Called by: views.v2_bib()
            TODO: merge with EzbV1Helper.build_query_dct() """
        query_dct = {
            'url': '%s://%s%s' % ( request.scheme,
                request.META.get( 'HTTP_HOST', '127.0.0.1' ),  # HTTP_HOST doesn't exist for client-tests
                request.META.get('REQUEST_URI', request.META['PATH_INFO'])
                ),
            'timestamp': str( rq_now ) }
        # self.build_stats_dct(
        #     query_dct['url'], request.META.get('HTTP_REFERER', None), request.META.get('HTTP_USER_AGENT', None), request.META.get('REMOTE_ADDR', None) )
        log.debug( 'query_dct, ```%s``' % pprint.pformat(query_dct) )
        return query_dct

    def prep_data( self, bib ):
        """ Grabs and processes data from Sierra.
            Called by: views.v2_bib() """
        return 'foo'

    def build_response_dct( self, data_dct, start_stamp ):
        """ Yup.
            Called by views.v2_bib() """
        return {}


    # def build_stats_dct( self, query_url, referrer, user_agent, ip ):
    #     """ Builds and logs data for stats.
    #         Called by build_query_dct() """
    #     stats_dct = { 'datetime': datetime.datetime.now().isoformat(), 'query': query_url, 'referrer': None, 'user_agent': user_agent, 'ip': ip }
    #     if referrer:
    #         output = urllib.parse.urlparse( referrer )
    #         stats_dct['referrer'] = output
    #     slog.info( json.dumps(stats_dct) )
    #     return

    def add_check_digit( self, raw_item_id ):
        """ Not yet used.
            Logic based on: <https://csdirect.iii.com/sierrahelp/Content/sril/sril_records_numbers.html> """
        data = str(raw_item_id).replace('-', '').replace(' ', '')  # Removes Hyphens and Spaces
        reversed = ''.join( reversed(data) )
        total = 0
        for counter,character in enumerate( reversed ):
            log.debug( f'character, `{character}`' )
            one_index = counter + 1
            log.debug( f'one_index, `{one_index}`' )
            multiplyer = one_index + 1
            log.debug( f'multiplyer, `{multiplyer}`' )
            multiplied = int(character) * multiplyer
            log.debug( f'multiplied, `{multiplied}`' )
            total += multiplied
            log.debug( f'total, `{total}`' )
        check_digit = (total % 11)
        if check_digit == 10:
            check_digit = 'x'
        log.debug( f'check_digit, `{check_digit}`' )
        return check_digit

    ## end class BibInfo

