""" Handles Sierra API connection """

import json, logging, os, sys, time

import requests
from availability_app import settings_app
from requests.auth import HTTPBasicAuth
from requests.exceptions import ReadTimeout as requests_ReadTimeout


log = logging.getLogger(__name__)


class SierraConnector( object ):

    def __init__( self ):
        # self.FILE_DOWNLOAD_DIR = os.environ['SBE__FILE_DOWNLOAD_DIR']
        # self.INVALID_PARAM_FILE_URL = os.environ['SBE__INVALID_PARAM_FILE_URL']
        # self.chunk_number_of_bibs = json.loads( os.environ['SBE__CHUNK_NUMBER_OF_BIBS_JSON'] )  # normally null -> None, or an int
        self.token = self.get_token()
        self.url = ''

    def get_token( self ):
        """ Gets API token.
            Called by controller.download_file() """
        token = 'init'
        # token_url = '%stoken' % self.API_ROOT_URL
        token_url = f'{settings_app.SIERRA_API_ROOT_URL}/token'
        log.debug( 'token_url, ```%s```' % token_url )
        try:
            r = requests.post( token_url,
                auth=HTTPBasicAuth( settings_app.SIERRA_API_HTTPBASIC_USERNAME, settings_app.SIERRA_API_HTTPBASIC_PASSWORD ),
                timeout=20 )
            log.debug( 'token r.content, ```%s```' % r.content )
            token = r.json()['access_token']
            log.debug( 'token, ```%s```' % token )
            return token
        except:
            log.exception( 'problem getting token...' )
            raise Exception( 'exception getting token' )

    # def make_bibrange_request( self, token, next_batch ):
    #     """ Forms and executes the bib-range query.
    #         Called by controller.download_file() """
    #     start_bib = next_batch['chunk_start_bib']
    #     end_bib = next_batch['chunk_end_bib'] if self.chunk_number_of_bibs is None else start_bib + self.chunk_number_of_bibs
    #     marc_url = '%sbibs/marc' % self.API_ROOT_URL
    #     payload = { 'id': '[%s,%s]' % (start_bib, end_bib), 'limit': (end_bib - start_bib) + 1, 'mapping': 'toc' }
    #     log.debug( 'payload, ```%s```' % payload )
    #     custom_headers = {'Authorization': 'Bearer %s' % token }
    #     r = requests.get( marc_url, headers=custom_headers, params=payload, timeout=30 )
    #     ( file_url, err ) = self.assess_bibrange_response( r )
    #     log.debug( 'returning file_url, ```%s```' % file_url )
    #     log.debug( 'returning err, ```%s```' % err )
    #     return ( file_url, err )

    def get_bibinfo( self, bib ):
        """ Gets json.
            Called by bib_v2.BibInfo.prep_data() """
        # url := s.URL + "/items?bibIds=" + bibsList
        # url = f'{settings_app.SIERRA_API_ROOT_URL}/items?bibIds=[{bib}]'
        sliced_bib = bib[1:]
        url = f'{settings_app.SIERRA_API_ROOT_URL}/items'
        log.debug( f'bib-url, ```{url}```' )
        custom_headers = {'Authorization': f'Bearer {self.token}' }
        payload = {
            'bibIds': f'{sliced_bib}',
            'fields': 'default,varFields,fixedFields'
            }  # HC: url += "&fields=default,varFields,fixedFields"
        try:
            r = requests.get( url, headers=custom_headers, params=payload, timeout=30 )
            log.debug( f'r.status_code, `{r.status_code}`; ```{r.url}```; r.content, ```{r.content}```' )
            self.url = r.url
            return r.json()
        except:
            log.exception( 'problem hitting api; traceback follows' )
            self.send_admin_email()
            return {}

    def assess_bibrange_response( self, r ):
        """ Not used; possible model for assessing response. """
        log.debug( 'r.status_code, `%s`' % r.status_code )
        log.debug( 'bib r.content, ```%s```' % r.content )
        file_url = err = None
        #
        if r.status_code == 500:
            try:
                response_message = r.json()['name']
            except Exception as e:
                message = 'could not read response-message, ```%s```; will exit script' % e
                # log.error( message )
                # raise Exception( message )
                log.warning( message )
                sys.exit()
            if response_message  == 'External Process Failed':
                log.warning( 'found response "%s"; returning this bib-range-response to continue' % response_message )
                err = r.content
                return ( file_url, err )
            elif response_message  == 'Rate exceeded for endpoint':  ## don't continue; stop until cron re-initiates
                message = 'found response "%s"; will exit script' % response_message
                # log.error( message )
                # raise Exception( message )
                log.warning( message )
                sys.exit()
            else:
                message = 'unhandled bib-range-response found, ```%s```; raising Exception' % response_message
                log.error( message )
                raise Exception( message )
        #
        if r.status_code == 200:
            try:
                data_dct = r.json()
            except Exception as e:
                message = 'response not json, ```%s```; raising Exception'
                log.error( message )
                raise Exception( message )
            try:
                if data_dct['outputRecords'] == 0:
                    log.info( 'no records found for this bib-range, returning bib-range-response to continue' )
                    err = r.content
                    return ( file_url, err )
            except Exception as e:
                message = '`outputrecords` not found in response; exception is ```%s```; raising Exception' % e
                log.error( message )
                raise Exception( message )
            try:  # happy-path
                file_url = data_dct['file']
                if file_url:
                    log.debug( 'normal file_url found, it is ```%s```' % file_url )
                    return ( file_url, err )
            except Exception as e:
                message = '`file` not found in response; exception is ```%s```; raising Exception' % e
                log.error( message )
                raise Exception( message )
        #
        if r.status_code is not 200 and r.status_code is not 500:
            message = 'unhandled status code, `%s`; raising Exception' % r.status_code
            log.error( message )
            raise Exception( message )

        ## end def assess_bibrange_response()

    ## end of SierraConnector()
