# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import json, logging, pprint
from availability_app import settings_app
from django.conf import settings as project_settings
from django.test import TestCase
from availability_app.lib.log_parser import LogParser


log = logging.getLogger(__name__)
TestCase.maxDiff = None


class LogParserTest( TestCase ):
    """ Checks LogParser() """

    def setUp(self):
        parser = LogParser()
        self.lines = self.load()

    def load(self):
        text_path = '%s/availability_app/lib/test_text.txt' % project_settings.BASE_DIR
        log.debug( 'text_path, `%s`' % text_path )
        entries = []
        with open( text_path ) as f:
            entries = f.readlines()
        return entries

    def test_find_segments(self):
        """ Checks raw line parsing into pieces. """
        self.assertEqual( 10, len(self.lines) )

    ## end LogParserTest()


class UrlTest( TestCase ):
    """ Checks basic urls. """

    def test_root_url_no_slash(self):
        """ Checks '/availability_api'. """
        response = self.client.get( '' )  # project root part of url is assumed
        self.assertEqual( 302, response.status_code )  # permanent redirect
        redirect_url = response._headers['location'][1]
        self.assertEqual(  '/info/', redirect_url )

    def test_root_url_slash(self):
        """ Checks '/availability_api/'. """
        response = self.client.get( '/' )  # project root part of url is assumed
        self.assertEqual( 302, response.status_code )  # permanent redirect
        redirect_url = response._headers['location'][1]
        self.assertEqual(  '/info/', redirect_url )

    def test_info(self):
        """ Checks '/availability_api/info/' """
        response = self.client.get( '/info/' )  # project root part of url is assumed
        # log.debug( 'response, ```%s```' % response )
        # log.debug( 'response.content, ```%s```' % response.content )
        response_dct = json.loads( response.content )
        self.assertEqual( 200, response.status_code )  # permanent redirect
        self.assertTrue(  b'time' in response.content )
        self.assertEqual( ['documentation', 'elapsed_time', 'version'], sorted(list(response_dct['response'].keys())) )

    ## end class UrlTest()


class V1_UrlTest( TestCase ):
    """ Checks isbn urls. """

    def test_found_isbn_1(self):
        """ Checks found isbn with two bibs'. """
        response = self.client.get( '/v1/isbn/{}/'.format( settings_app.TEST_ISBN_FOUND_01) )  # project root part of url is assumed
        content = response.content.decode('utf-8')
        self.assertTrue( '"bib": "b1815113"' in content )
        self.assertTrue( '"bib": "b2767927"' in content )
        self.assertTrue( 'Zen and the art of motorcycle maintenance' in content )

    def test_found_isbn_2(self):
        """ Checks found isbn with multiple pymarc Records, two of which don't have bibliographic records. """
        response = self.client.get( '/v1/isbn/{}/'.format( settings_app.TEST_ISBN_FOUND_02) )  # project root part of url is assumed
        content = response.content.decode('utf-8')
        self.assertTrue( '"bib": "b2696893"' in content )
        self.assertTrue( '"bib": "b2814930"' in content )
        self.assertTrue( 'Kongolese Saint Anthony' in content )
        self.assertTrue( 'Africa and Africans' in content )

    # def test_invalid_key(self):
    #     """ Checks non 'isbn' or 'oclc' key. """
    #     response = self.client.get( '/v2/foo/{}/'.format( settings_app.TEST_ISBN_FOUND_01) )  # project root part of url is assumed
    #     response_dct = json.loads( response.content )
    #     self.assertEqual( 'query_key bad', response_dct['response']['error'] )

    ## end class V1_UrlTest()
