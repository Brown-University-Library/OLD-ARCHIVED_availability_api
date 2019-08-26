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

    def build_stats_dct( self, query_url, referrer, user_agent, ip ):
        """ Builds and logs data for stats.
            Called by build_query_dct() """
        stats_dct = { 'datetime': datetime.datetime.now().isoformat(), 'query': query_url, 'referrer': None, 'user_agent': user_agent, 'ip': ip }
        if referrer:
            output = urllib.parse.urlparse( referrer )
            stats_dct['referrer'] = output
        slog.info( json.dumps(stats_dct) )
        return

    ## end class BibInfo

