"""
Helper for views.v2_bib()
"""

import datetime, json, logging, operator, os, pprint

import requests
from availability_app.lib.sierra_api import SierraConnector


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
        raw_data = sierra.get_bib_items_info( bib[1:] )  # removes the 'b' of the bib-number
        items = self.summarize_data( raw_data, bib )
        response_dct = { 'items': items, 'items_count': len(items), 'sierra_api': raw_data, 'sierra_api_query': sierra.url }
        log.debug( f'response_dct, ```{response_dct}```' )
        return response_dct

    def summarize_data( self, raw_data, bib ):
        """ Extracts essential data from sierra-api data.
            Called by prep_data() """
        items = []
        initial_entries = raw_data['entries']  # initial_entries is a list of dicts
        sorted_entries = self.sort_entries( initial_entries, bib )
        for entry in sorted_entries:
            item_dct = {
                'barcode': entry['barcode'].replace( ' ', '' ),
                'callnumber': self.build_callnumber( entry ),
                'item_id': self.build_item_id( entry['id'] ),
                'location': entry['location']['name'],
                # 'status': entry['status']['display']
                'status': self.build_status( entry['status'] )
            }
            items.append( item_dct )
        log.debug( f'items, ```{pprint.pformat(items)}```' )
        return items

    def sort_entries( self, initial_entries, bib ):
        """ Gets the 945 order, and sorts entries according to that order.
            Called by summarize_data() """
        ordered_945_item_ids = self.get_945_item_id_list( bib )
        order_dct = { order_945: index for index, order_945 in enumerate(ordered_945_item_ids) }
        log.debug( f'order_dct, ```{pprint.pformat(order_dct)}```' )
        sorted_entries = sorted( initial_entries, key=lambda x: order_dct[x['id']] )
        log.debug( f'sorted_entries, ```{pprint.pformat(sorted_entries)}```' )
        return sorted_entries

    def build_callnumber( self, entry ):
        """ Adds data to default callnumber field.
            Called by summarize_data() """
        if 'callNumber' not in entry.keys():
            built_callnumber = 'no_callnumber_found'
        else:
            initial_built_callnumber = self.start_callnumber_build( entry )
            addition2 = ''
            if 'fixedFields' in entry.keys():
                for ( key, value_dct ) in entry['fixedFields'].items():
                    if key == '58':  # then value_dct, eg, {"label": "COPY #", "value": "2"}
                        if int( value_dct['value'] ) > 1:
                            addition2 = f'c.{value_dct["value"]}'   # resulting in, eg, c.2
                            break
            built_callnumber = f'{initial_built_callnumber} {addition2}'.strip()
        log.debug( f'built_callnumber, `{built_callnumber}`' )
        return built_callnumber

    def start_callnumber_build( self, entry ):
        """ Checks 'v' varField.
            Called by build_callnumber() """
        initial_callnumber = entry['callNumber']
        addition = ''
        if 'varFields' in entry.keys():
            for var_field_dct in entry['varFields']:
                if var_field_dct.get( 'fieldTag', '' ) == 'v':
                    addition = var_field_dct['content']  # eg "Box 10"
                    break
        initial_built_callnumber = f'{initial_callnumber} {addition}'.strip()
        log.debug( f'initial_built_callnumber, `{initial_built_callnumber}`' )
        return initial_built_callnumber

    # def build_callnumber( self, entry ):
    #     """ Adds data to default callnumber field.
    #         Called by summarize_data() """
    #     try:
    #         if 'callNumber' not in entry.keys():
    #             built_callnumber = 'no_callnumber_found'
    #         else:
    #             initial_callnumber = entry['callNumber']
    #             addition = ''
    #             if 'varFields' in entry.keys():
    #                 for var_field_dct in entry['varFields']:
    #                     if var_field_dct.get( 'fieldTag', '' ) == 'v':
    #                         addition = var_field_dct['content']  # eg "Box 10"
    #             built_callnumber = f'{initial_callnumber} {addition}'.strip()
    #             addition2 = ''
    #             if 'fixedFields' in entry.keys():
    #                 for ( key, value_dct ) in entry['fixedFields'].items():
    #                     if key == '58':  # then value_dct, eg, {"label": "COPY #", "value": "2"}
    #                         if int( value_dct['value'] ) > 1:
    #                             addition2 = f'c.{value_dct["value"]}'   # resulting in, eg, c.2
    #             built_callnumber = f'{built_callnumber} {addition2}'.strip()
    #         log.debug( f'built_callnumber, `{built_callnumber}`' )
    #         return built_callnumber
    #     except Exception as e:
    #         log.exception( 'problem building callnumber; traceback follows' )
    #         log.debug( f'entry, ```{pprint.pformat(entry)}```' )
    #         raise Exception( e )

    def build_item_id( self, initial_item_id ):
        """ Adds '.i' and check-digit to item-id.
            Called by summarize_data() """
        check_digit = self.build_check_digit( initial_item_id )
        built_item_id = f'i{initial_item_id}{check_digit}'
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
            one_index = counter + 1; log.debug( f'one_index, `{one_index}`' )
            multiplyer = one_index + 1; log.debug( f'multiplyer, `{multiplyer}`' )
            multiplied = int(character) * multiplyer; log.debug( f'multiplied, `{multiplied}`' )
            total += multiplied
            log.debug( f'total, `{total}`' )
        check_digit = (total % 11)
        if check_digit == 10:
            check_digit = 'x'
        log.debug( f'check_digit, `{check_digit}`' )
        return check_digit

    def build_status( self, status_dct ):
        """ Examines dct & returns display status.
            Called by summarize_data() """
        if 'duedate' in status_dct.keys():
            status = f'DUE {status_dct["duedate"][0:10]}'  # from "2019-09-30T08:00:00Z" to '2019-09-30'
        else:
            status = status_dct['display']
        log.debug( 'status, `{status}`' )
        return status

    def build_response_dct( self, data_dct, start_stamp ):
        """ Yup.
            Called by views.v2_bib() """
        response_dct = data_dct
        response_dct['time_taken'] = str( datetime.datetime.now() - start_stamp )
        log.debug( f'response_dct, ```{pprint.pformat(response_dct)}```' )
        return response_dct

    # def build_stats_dct( self, query_url, referrer, user_agent, ip ):
    #     """ Builds and logs data for stats. Not yet implemented for this url-path
    #         Called by build_query_dct() """
    #     stats_dct = { 'datetime': datetime.datetime.now().isoformat(), 'query': query_url, 'referrer': None, 'user_agent': user_agent, 'ip': ip }
    #     if referrer:
    #         output = urllib.parse.urlparse( referrer )
    #         stats_dct['referrer'] = output
    #     slog.info( json.dumps(stats_dct) )
    #     return

    def get_945_item_id_list( self, bib ):
        """ Not yet used; experimental. """
        item_ids = []
        url = f'https://search.library.brown.edu/catalog/{bib}.json'
        r = requests.get( url )
        dct = r.json()
        marc_string = dct['response']['document']['marc_display']
        marc_dct = json.loads( marc_string )
        for field_dct in marc_dct['fields']:
            ( key, value_dct ) = list( field_dct.items() )[0]
            if key == '945':
                for subfield_dct in value_dct['subfields']:
                    ( key2, value2 ) = list( subfield_dct.items() )[0]
                    if key2 == 'y':
                        item_ids.append( value2[2:-1] )  # raw value2 is like '.i159930728' -- this drops the '.i' and the check-digit
                        break
        log.debug( f'item_ids, ```{item_ids}```' )
        return item_ids

    ## end class BibInfo

