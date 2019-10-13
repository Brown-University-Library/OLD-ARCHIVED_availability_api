import logging, time
import asks, trio


log = logging.getLogger( __name__ )


class AsyncHelper():

    def __init__(self):
        pass

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
        log.debug( 'total time: %s' % str(time.time() - start_time) )

    async def fetch( self, item, results_holder_dct ):
        """ Handles work of hitting the urls.
            Called by manage_calls() """
        log.debug( f'starting fetch() with item, ```{item}```' )
        ( label, url ) = ( item[0], item[1] )
        log.debug( f'start: url, ```{url}```' )
        response = await asks.get( url )
        # print("Finished: ", url, len(response.content))
        log.debug( 'finished: url, ```%s```; status_code, `%s`' % (url, response.status_code) )

    ## end class AsyncHelper()
