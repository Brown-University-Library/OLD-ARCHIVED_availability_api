"""
Helper for views.v2_bib()
"""

import datetime, logging, os, pprint

from availability_app.lib.sierra_api import SierraConnector
# from availability_app import settings_app


log = logging.getLogger(__name__)


class BibItemsInfo:

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
        sierra = SierraConnector()  # instantiated here to get fresh token
        raw_data = sierra.get_bib_items_info( bib )
        items = self.summarize_data( raw_data )
        response_dct = { 'items': items, 'items_count': len(items), 'sierra_api': raw_data, 'sierra_api_query': sierra.url }
        log.debug( f'response_dct, ```{response_dct}```' )
        return response_dct

    def summarize_data( self, raw_data ):
        """ Extracts essential data from sierra-api data.
            Called by prep_data() """
        items = []
        for entry in raw_data['entries']:
            item_dct = {
                'barcode': entry['barcode'],
                'callnumber': self.build_callnumber( entry ),
                'item_id': self.build_item_id( entry['id'] ),
                'location': entry['location']['name'],
                'status': entry['status']['display']
            }
            items.append( item_dct )
        log.debug( f'items, ```{pprint.pformat(items)}```' )
        return items

    def build_callnumber( self, entry ):
        """ Adds data to default callnumber field.
            Called by summarize_data() """
        initial_callnumber = entry['callNumber']
        addition = ''
        if 'varFields' in entry.keys():
            for var_field_dct in entry['varFields']:
                if var_field_dct.get( 'fieldTag', '' ) == 'v':
                    addition = var_field_dct['content']  # i.e. "Box 10"
        built_callnumber = f'{initial_callnumber} {addition}'.strip()
        log.debug( f'built_callnumber, `{built_callnumber}`' )
        return built_callnumber

    def build_item_id( self, initial_item_id ):
        """ Adds '.i' and check-digit to item-id.
            Called by summarize_data() """
        check_digit = self.build_check_digit( initial_item_id )
        built_item_id = f'.i{initial_item_id}{check_digit}'
        log.debug( 'built_item_id, `{built_item_id}`' )
        return built_item_id

    def build_check_digit( self, raw_item_id ):
        """ Calculates check-digit.
            Logic based on: <https://csdirect.iii.com/sierrahelp/Content/sril/sril_records_numbers.html>
            Called by build_item_id() """
        data = str(raw_item_id).replace('-', '').replace(' ', '')  # Removes Hyphens and Spaces
        reversed_data = ''.join( reversed(data) )
        total = 0
        for counter,character in enumerate( reversed_data ):
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

    def build_response_dct( self, data_dct, start_stamp ):
        """ Yup.
            Called by views.v2_bib() """
        response_dct = data_dct
        # response_dct = {
        #     'time_taken': str( datetime.datetime.now() - start_stamp ),
        #     'sierra_api': data_dct
        #      }
        response_dct['time_taken'] = str( datetime.datetime.now() - start_stamp )
        log.debug( f'response_dct, ```{pprint.pformat(response_dct)}```' )
        return response_dct

    # def build_stats_dct( self, query_url, referrer, user_agent, ip ):
    #     """ Builds and logs data for stats.
    #         Called by build_query_dct() """
    #     stats_dct = { 'datetime': datetime.datetime.now().isoformat(), 'query': query_url, 'referrer': None, 'user_agent': user_agent, 'ip': ip }
    #     if referrer:
    #         output = urllib.parse.urlparse( referrer )
    #         stats_dct['referrer'] = output
    #     slog.info( json.dumps(stats_dct) )
    #     return

    ## end class BibInfo

