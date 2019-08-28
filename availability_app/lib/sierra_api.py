""" Handles Sierra API connection """

import json, logging, os, sys, time

import requests
from availability_app import settings_app
from requests.auth import HTTPBasicAuth
from requests.exceptions import ReadTimeout as requests_ReadTimeout


log = logging.getLogger(__name__)


class SierraConnector( object ):

    def __init__( self ):
        self.token = self.get_token()
        self.url = ''

    def get_token( self ):
        """ Gets API token.
            Called by controller.download_file() """
        token = 'init'
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

    def get_bib_items_info( self, sliced_bib ):  # bib doesn't contain initial 'b'
        """ Gets json.
            Called by bib_items_v2.BibInfo.prep_data() """
        url = f'{settings_app.SIERRA_API_ROOT_URL}/items'
        custom_headers = {'Authorization': f'Bearer {self.token}' }
        payload = {
            'bibIds': f'{sliced_bib}',
            'fields': 'default,varFields,fixedFields',
            'deleted': 'false',
            'suppressed': 'false' }
        try:
            r = requests.get( url, headers=custom_headers, params=payload, timeout=30 )
            log.debug( f'r.status_code, `{r.status_code}`; ```{r.url}```; r.content, ```{r.content}```' )
            self.url = r.url
            return r.json()
        except:
            log.exception( 'problem hitting api; traceback follows' )
            self.send_admin_email()
            return {}

    def send_admin_email( self ):
        """ TODO """
        pass
        return

    ## end of SierraConnector()
