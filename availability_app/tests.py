# -*- coding: utf-8 -*-

import datetime, json, logging, pprint
from availability_app import settings_app
from django.conf import settings as project_settings
from django.test import TestCase
from availability_app.lib.log_parser import LogParser


log = logging.getLogger(__name__)
TestCase.maxDiff = None


class ValidityTest( TestCase ):
    """ Checks submitted identifier. """

    def setUp(self):
        self.parser = LogParser()

    def test_good_short_isbn(self):
        isbn = '0688002307'
        self.assertEqual( True, self.parser.validate_isbn(isbn) )

    def test_good_long_isbn(self):
        isbn = '9780688002305'
        self.assertEqual( True, self.parser.validate_isbn(isbn) )

    def test_bad_isbn(self):
        isbn = '123'
        self.assertEqual( False, self.parser.validate_isbn(isbn) )

    ## end ValidityTest()


class LogParserTest( TestCase ):
    """ Checks LogParser() """

    def setUp(self):
        self.parser = LogParser()
        self.lines = self.load()

    def load(self):
        text_path = '%s/availability_app/lib/test_text.txt' % project_settings.BASE_DIR
        log.debug( 'text_path, `%s`' % text_path )
        entries = []
        with open( text_path ) as f:
            entries = f.readlines()
        return entries

    def test_make_date(self):
        """ Checks string-to-date conversion. """
        dt = datetime.datetime( 2018, 9, 10, 15, 44, 47, 9965 )
        # self.assertEqual( dt, self.parser.get_date('[02/Aug/2018 15:21:56]') )
        self.assertEqual( dt, self.parser.get_date('2018-09-10T15:44:47.009965') )

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
