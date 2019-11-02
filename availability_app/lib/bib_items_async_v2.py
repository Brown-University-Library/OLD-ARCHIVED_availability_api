"""
Helper for views.v2_bib()
"""

import datetime, json, logging, operator, os, pprint, time

import asks, requests, trio
from asks import BasicAuth as asksBasicAuth
from availability_app import settings_app
from availability_app.lib.sierra_api import SierraAsyncConnector
from django.conf import settings as project_settings


log = logging.getLogger(__name__)


class DataFetcher:
    """ Manages multiple api requests.
        Called by BibItemsInfoAsync.manage_data_calls() """

    def __init__( self, bibnum ):
        self.bibnum = bibnum
        self.results_dct = {}
        self.total_time_taken = None

    async def call_urls( self ):
        """ Triggers hitting urls concurrently.
            Called by manage_data_calls() """
        log.debug( 'starting call_urls()' )
        start_time = time.time()
        results_holder_dct = {}  # receives fetch() responses as they're produced
        log.debug( 'round ONE async calls about to commence' )
        async with trio.open_nursery() as nursery:
            nursery.start_soon( self.fetch_945_data, results_holder_dct )
            nursery.start_soon( self.fetch_sierra_token, results_holder_dct )  # NOTE: after getting token, fetch_sierra_token() will set up its own nursery to call the bib-api and the items-api.
        log.debug( f'final results_holder_dct, ```{pprint.pformat(results_holder_dct)}```' )
        self.total_time_taken = str( time.time() - start_time )
        log.debug( f'total time: taken ```{self.total_time_taken}```' )
        self.results_dct = results_holder_dct
        return

    async def fetch_945_data( self, results_holder_dct ):
        """ Obtains 945 data for sorting items.
            Called by call_urls() """
        log.debug( 'starting fetch_945_data()' )
        log.debug( f'initial results_holder_dct, ```{results_holder_dct}```' )
        fetch_start_time = time.time()
        item_ids = []
        try:
            url = f'https://search.library.brown.edu/catalog/{self.bibnum}.json'
            rsp = await asks.get( url, timeout=2 )
            self.process_945_data( rsp, item_ids )
        except Exception as e:
            status_code = repr(e)
            log.exception( '`get` failed; traceback follows; processing will continue' )
        fetch_time_taken = str( time.time() - fetch_start_time )
        fetch_holder_dct = { 'josiah_945_lst': item_ids, 'time_taken': fetch_time_taken }
        log.debug( f'fetch finished: fetch_holder_dct, ```{fetch_holder_dct}```' )
        results_holder_dct['josiah_945_results'] = fetch_holder_dct
        log.debug( f'fetch finished: results_holder_dct, ```{results_holder_dct}```' )
        return

    def process_945_data( self, rsp, item_ids ):
        """ Extracts 945 items from response.
            Called by fetch_945_data() """
        dct = rsp.json()
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
        return

    async def fetch_sierra_token( self, results_holder_dct ):
        """ Obtains auth-token for later sierra calls.
            Called by call_urls() """
        log.debug( 'starting fetch_sierra_token()' )
        log.debug( f'initial results_holder_dct, ```{results_holder_dct}```' )
        fetch_start_time = time.time()
        auth_token = {}
        try:
            # sierra = SierraAsyncConnector()  # instantiated here to get fresh token
            # response = await asks.post( 'https://httpbin.org/delay/.2', timeout=2 )
            # status_code = response.status_code
            token_url = f'{settings_app.SIERRA_API_ROOT_URL}/token'
            log.debug( 'token_url, ```%s```' % token_url )
            # asksBasicAuth -- <https://asks.readthedocs.io/en/latest/overview-of-funcs-and-args.html#authing>
            usr_pw = ( settings_app.SIERRA_API_HTTPBASIC_USERNAME, settings_app.SIERRA_API_HTTPBASIC_PASSWORD )
            rsp = await asks.post(
                token_url,
                auth=asksBasicAuth( usr_pw ),
                timeout=10 )
            log.debug( f'token rsp.content, ```{rsp.content}```' )
            auth_token = rsp.json()['access_token']
            log.debug( f'auth_token, ```{auth_token}```' )
        except Exception as e:
            log.exception( 'accessing token failed; traceback follows...' )
            raise Exception( 'exception getting token' )
        fetch_time_taken = str( time.time() - fetch_start_time )
        fetch_holder_dct = { 'sierra_token_value': auth_token, 'time_taken': fetch_time_taken }
        log.debug( f'fetch finished: fetch_holder_dct, ```{fetch_holder_dct}```' )
        results_holder_dct['sierra_token_results'] = fetch_holder_dct
        log.debug( f'fetch finished: results_holder_dct, ```{results_holder_dct}```' )
        log.debug( 'round TWO async calls about to commence' )
        async with trio.open_nursery() as nursery:
            nursery.start_soon( self.fetch_sierra_bib_data, auth_token, results_holder_dct )
            nursery.start_soon( self.fetch_sierra_item_data, auth_token, results_holder_dct )
        return

    async def fetch_sierra_bib_data( self, auth_token, results_holder_dct ):
        """ Returns auth-token for later sierra calls.
            Called by fetch_sierra_token() """
        log.debug( 'starting fetch_sierra_bib_data()' )
        log.debug( f'initial results_holder_dct, ```{results_holder_dct}```' )
        fetch_start_time = time.time()
        bib_dct = {}
        try:
            sliced_bib = self.bibnum[1:]  # removes initial 'b'
            url = f'{settings_app.SIERRA_API_ROOT_URL}/bibs/?id={sliced_bib}'
            custom_headers = {'Authorization': f'Bearer {auth_token}' }
            rsp = await asks.get( url, headers=custom_headers, timeout=10 )
            log.debug( f'rsp.status_code, `{rsp.status_code}`; ```{rsp.url}```; rsp.content, ```{rsp.content}```' )
            bib_dct = rsp.json()
        except Exception as e:
            status_code = repr(e)
            log.exception( '`get` failed; traceback follows; processing will continue' )
        fetch_time_taken = str( time.time() - fetch_start_time )
        fetch_holder_dct = { 'sierra_bib_data': bib_dct, 'time_taken': fetch_time_taken }
        log.debug( f'fetch finished: fetch_holder_dct, ```{fetch_holder_dct}```' )
        results_holder_dct['sierra_bib_results'] = fetch_holder_dct
        log.debug( f'fetch finished: results_holder_dct, ```{results_holder_dct}```' )
        return

    async def fetch_sierra_item_data( self, auth_token, results_holder_dct ):
        """ Returns auth-token for later sierra calls.
            Called by fetch_sierra_token() """
        log.debug( 'starting fetch_sierra_item_data()' )
        log.debug( f'initial results_holder_dct, ```{results_holder_dct}```' )
        fetch_start_time = time.time()
        try:
            sliced_bib = self.bibnum[1:]  # removes initial 'b'
            url = f'{settings_app.SIERRA_API_ROOT_URL}/items'
            custom_headers = {'Authorization': f'Bearer {auth_token}' }
            payload = {
                'bibIds': f'{sliced_bib}',
                'fields': 'default,varFields,fixedFields',
                'deleted': 'false', 'suppressed': 'false', 'limit': '300' }
            rsp = await asks.get( url, headers=custom_headers, params=payload, timeout=10 )
            raw_items_dct = rsp.json()
            log.debug( f'rsp.status_code, `{rsp.status_code}`; ```{rsp.url}```; rsp.content, ```{rsp.content}```' )
        except Exception as e:
            status_code = repr(e)
            log.exception( '`get` failed; traceback follows; processing will continue' )
        fetch_time_taken = str( time.time() - fetch_start_time )
        fetch_holder_dct = { 'sierra_item_data': raw_items_dct, 'time_taken': fetch_time_taken }
        log.debug( f'fetch finished: fetch_holder_dct, ```{fetch_holder_dct}```' )
        results_holder_dct['sierra_item_results'] = fetch_holder_dct
        log.debug( f'fetch finished: results_holder_dct, ```{results_holder_dct}```' )
        return

    ## end class DataFetcher


class BibItemsInfoAsync:

    def __init__( self ):
        log.debug( 'initializing BibItemsInfoAsync instance' )
        self.results_dct = {}
        self.total_time_taken = None
        self.bibnum = ''

    def build_query_dct( self, request, rq_now ):
        """ Builds query-dct part of response.
            Called by: views.v2_bib_items_async()
            TODO: merge with other identical methods() """
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

    def manage_data_calls( self, bibnum ):
        """ Initiates async manager.
            Called by views.v2_bib_items_async()
            (Bridge between sync and async.) """
        log.debug( 'about to call trio.run()' )
        fetcher = DataFetcher( bibnum )
        self.bibnum = 'FOO'  # remove if not needed
        trio.run( fetcher.call_urls )
        # self.results_dct = fetcher.results_dct
        fetched_data = fetcher.results_dct
        log.debug( f'results_dct, see recent DataFetcher.call_urls() log-entry' )
        return fetched_data

    def prep_data( self, raw_data_dct, host ):
        """ Extracts data for response.
            Called by views.v2_bib_items_async() """
        log.debug( f'raw_data_dct.keys(), ```{sorted( raw_data_dct.keys() )}```' )
        summarized_bib_dct = self.summarize_bib_data( raw_data_dct['sierra_bib_results'] )
        summarized_item_lst = self.summarize_item_data( raw_data_dct['sierra_item_results'], raw_data_dct['josiah_945_results'] )
        response_dct = { 'bib': summarized_bib_dct, 'items': summarized_item_lst, 'items_count': len(summarized_item_lst) }
        if project_settings.DEBUG == True and host[0:9] == '127.0.0.1':  # useful for development
            response_dct['sierra-bibitems-api'] = raw_data_dct['sierra_item_results']['sierra_item_data']
        log.debug( f'response_dct, ```{response_dct}```' )
        return response_dct

    def summarize_bib_data( self, raw_bib_data ):
        """ Extracts essential data from sierra-api bib data.
            Called by prep_data() """
        try:
            entry = raw_bib_data['sierra_bib_data']['entries'][0]
            title = entry['title']
            if title[-1] == ',':
                title = title[0:-1]
            bib_dct = { 'title': title, 'author': entry['author'], 'url': f'https://search.library.brown.edu/catalog/b{entry["id"]}' }
        except:
            log.exception( 'problem building bib_dct; traceback follows but processing will continue' )
            bib_dct = { 'title': 'title unavailable', 'author': 'author unavailable', 'url': 'url unavailable' }
        log.debug( f'bib_dct, ```{bib_dct}```' )
        return bib_dct

    def summarize_item_data( self, sierra_item_results, josiah_945_data ):
        """ Extracts essential data from sierra-api items data.
            Called by prep_data() """
        items = []
        initial_entries = sierra_item_results['sierra_item_data']['entries']  # initial_entries is a list of dicts
        sorted_entries = self.sort_entries( initial_entries, josiah_945_data )
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

    def sort_entries( self, initial_entries, josiah_945_data ):
        """ Gets the 945 order, and sorts entries according to that order.
            Called by summarize_item_data() """
        # ordered_945_item_ids = self.get_945_item_id_list( bib )
        ordered_945_item_ids = josiah_945_data['josiah_945_lst']
        order_dct = { order_945: index for index, order_945 in enumerate(ordered_945_item_ids) }
        log.debug( f'order_dct, ```{pprint.pformat(order_dct)}```' )
        sorted_entries = sorted( initial_entries, key=lambda x: order_dct[x['id']] )
        log.debug( f'sorted_entries, ```{pprint.pformat(sorted_entries)}```' )
        return sorted_entries

    def build_callnumber( self, entry ):
        """ Adds data to default callnumber field.
            Called by summarize_item_data() """
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

    def build_item_id( self, initial_item_id ):
        """ Adds '.i' and check-digit to item-id.
            Called by summarize_item_data() """
        check_digit = self.build_check_digit( initial_item_id )
        built_item_id = f'i{initial_item_id}{check_digit}'
        log.debug( 'built_item_id, `{built_item_id}`' )
        return built_item_id

    def build_check_digit( self, raw_item_id ):
        """ Calculates check-digit.
            Logic based on: <https://csdirect.iii.com/sierrahelp/Content/sril/sril_records_numbers.html>
            Reverses the string, then, for each character-position (now from left-to-right), determines a value and adds it to a total, and finally applies a modulo.
            Called by build_item_id() """
        log.debug( f'raw_item_id, `{raw_item_id}`' )
        data = str(raw_item_id).replace('-', '').replace(' ', '')  # Removes Hyphens and Spaces
        reversed_data = ''.join( reversed(data) )
        total = 0
        for counter,character in enumerate( reversed_data ):
            one_index = counter + 1
            multiplyer = one_index + 1
            multiplied = int(character) * multiplyer
            total += multiplied
            log.debug( f'after character, `{character}` -- total currently, `{total}`' )
        check_digit = (total % 11)
        if check_digit == 10:
            check_digit = 'x'
        log.debug( f'check_digit, `{check_digit}`' )
        return check_digit

    def build_status( self, status_dct ):
        """ Examines dct & returns display status.
            Called by summarize_item_data() """
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

    # async def call_urls( self, bibnum ):
    #     """ Triggers hitting urls concurrently.
    #         Called by manage_data_calls() """
    #     log.debug( 'starting call_urls()' )
    #     start_time = time.time()
    #     results_holder_dct = {}  # receives fetch() responses as they're produced
    #     log.debug( 'round ONE async calls about to commence' )
    #     async with trio.open_nursery() as nursery:
    #         nursery.start_soon( self.fetch_sierra_token, results_holder_dct )
    #         nursery.start_soon( self.fetch_945_data, bibnum, results_holder_dct )
    #     log.debug( 'round TWO async calls about to commence' )
    #     async with trio.open_nursery() as nursery:
    #         nursery.start_soon( self.fetch_sierra_bib_data, bibnum, results_holder_dct )
    #         nursery.start_soon( self.fetch_sierra_item_data, bibnum, results_holder_dct )
    #     log.debug( f'results_holder_dct, ```{pprint.pformat(results_holder_dct)}```' )
    #     self.total_time_taken = str( time.time() - start_time )
    #     log.debug( f'total time: taken ```{self.total_time_taken}```' )
    #     self.results_dct = results_holder_dct
    #     return

    ## end class BibInfo

