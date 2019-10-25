import logging, pprint, time
import asks, trio


log = logging.getLogger( __name__ )


class AsyncHelper():

    def __init__(self):
        self.results_dct = {}
        self.total_time_taken = None

    def process_urls( self, url_dct ):
        """ Initiates async manager.
            Called by views.concurrency_test()
            (Bridge between sync and async.) """
        log.debug( 'about to call trio.run()' )
        trio.run( self.manage_calls, url_dct )

    async def manage_calls( self, url_dct ):
        """ Triggers hitting urls concurrently.
            Called by process_urls() """
        log.debug( 'starting manage_calls()' )
        start_time = time.time()
        results_holder_dct = {}  # receives fetch() responses as they're produced
        async with trio.open_nursery() as nursery:
            for item in url_dct.items():
                nursery.start_soon( self.fetch, item, results_holder_dct )
        log.debug( f'results_holder_dct, ```{pprint.pformat(results_holder_dct)}```' )
        self.total_time_taken = str( time.time() - start_time )
        log.debug( f'total time: taken ```{self.total_time_taken}```' )
        self.results_dct = results_holder_dct
        return

    async def fetch( self, item, results_holder_dct ):
        """ Handles work of hitting the urls.
            Called by manage_calls() """
        log.debug( f'starting fetch() with item, ```{item}```' )
        fetch_start_time = time.time()
        ( label, url ) = ( item[0], item[1] )
        log.debug( f'start: url, ```{url}```' )
        try:
            response = await asks.get( url, timeout=2 )
            status_code = response.status_code
        except Exception as e:
            status_code = repr(e)
            log.exception( '`get` failed; traceback follows; processing will continue' )
        fetch_time_taken = str( time.time() - fetch_start_time )
        # holder_result_dct = { 'url': url, 'response_status_code': response.status_code, 'time_taken': fetch_time_taken }
        holder_result_dct = { 'url': url, 'response_status_code': status_code, 'time_taken': fetch_time_taken }
        log.debug( f'finished: holder_result_dct, ```{holder_result_dct}```' )
        results_holder_dct[label] = holder_result_dct
        return

    ## end class AsyncHelper()
