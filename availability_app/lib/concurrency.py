import logging, pprint, time
import asks, trio


log = logging.getLogger( __name__ )


class AsyncHelper():

    def __init__(self):
        self.results_dct = {}

    def process_urls( self, url_dct ):
        """ Initiates async manager.
            Called by views.concurrency_test()
            (Bridge between sync and async.) """
        log.debug( 'about to call trio.run()' )
        trio.run( self.manage_calls, url_dct )

    async def manage_calls( self, url_dct ):
        """ Hits urls concurrently.
            Called by process_urls() """
        log.debug( 'starting manage_calls()' )
        start_time = time.time()
        results_holder_dct = {}
        async with trio.open_nursery() as nursery:
            for item in url_dct.items():
                nursery.start_soon( self.fetch, item, results_holder_dct )
        log.debug( f'results_holder_dct, ```{pprint.pformat(results_holder_dct)}```' )
        log.debug( 'total time: %s' % str(time.time() - start_time) )
        self.results_dct = results_holder_dct
        return

    async def fetch( self, item, results_holder_dct ):
        """ Handles work of hitting the urls.
            Called by manage_calls() """
        log.debug( f'starting fetch() with item, ```{item}```' )
        ( label, url ) = ( item[0], item[1] )
        log.debug( f'start: url, ```{url}```' )
        response = await asks.get( url )
        holder_result_dct = { 'url': url, 'response_status_code': response.status_code }
        log.debug( 'finished: holder_result_dct, ```{holder_result_dct}```' )
        results_holder_dct[label] = holder_result_dct
        return

    ## end class AsyncHelper()
