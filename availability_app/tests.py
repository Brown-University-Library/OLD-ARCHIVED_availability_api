# -*- coding: utf-8 -*-

import datetime, json, logging, pprint
from availability_app import settings_app
from availability_app.lib.bib_items_v2 import BibItemsInfo
from availability_app.lib.ezb_v1_handler import EzbV1Helper, Validator
from availability_app.lib.log_parser import LogParser
from django.conf import settings as project_settings
from django.test import TestCase


log = logging.getLogger(__name__)
TestCase.maxDiff = None


class BibItemsTest( TestCase ):
    """ Checks module which prepares bib-items for api response. """

    def setUp(self):
        self.bib_info = BibItemsInfo()

    def test_no_callnumber(self):
        entry = {'barcode': 'JH 153S ',
         'bibIds': ['3100638'],
         'createdDate': '2012-07-18T13:17:00Z',
         'deleted': False,
         'fixedFields': {'108': {'label': 'OPACMSG', 'value': ' '},
                         '109': {'label': 'Circ 7/2015+', 'value': '1'},
                         '110': {'label': 'Circ 7/2013-6/2015', 'value': '0'},
                         '127': {'label': 'AGENCY', 'value': '0'},
                         '161': {'label': 'VI CENTRAL', 'value': '0'},
                         '162': {'label': 'IR DIST LEARN SAME SITE', 'value': '0'},
                         '264': {'label': 'Holdings Item Tag', 'value': '6'},
                         '265': {'label': 'Inherit Location', 'value': 'false'},
                         '57': {'label': 'BIB HOLD', 'value': 'false'},
                         '58': {'label': 'COPY #', 'value': '1'},
                         '59': {'label': 'ICODE1', 'value': '0'},
                         '60': {'label': 'ICODE2', 'value': '-'},
                         '61': {'display': 'Hay Annex',
                                'label': 'I TYPE',
                                'value': '99'},
                         '62': {'label': 'PRICE', 'value': '0.000000'},
                         '64': {'label': 'OUT LOC', 'value': '300'},
                         '67': {'label': 'LPATRON', 'value': '1117435'},
                         '68': {'label': 'LCHKIN', 'value': '2019-02-27T20:13:09Z'},
                         '70': {'label': 'IN LOC', 'value': '300'},
                         '74': {'label': 'IUSE3', 'value': '0'},
                         '76': {'label': 'Total Circ 1995+', 'value': '1'},
                         '77': {'label': 'TOT RENEW', 'value': '0'},
                         '78': {'label': 'LOUTDATE', 'value': '2019-02-27T20:12:59Z'},
                         '79': {'display': 'ANNEX HAY',
                                'label': 'LOCATION',
                                'value': 'qhs'},
                         '80': {'label': 'REC TYPE', 'value': 'i'},
                         '81': {'label': 'RECORD #', 'value': '16565480'},
                         '83': {'label': 'CREATED', 'value': '2012-07-18T13:17:00Z'},
                         '84': {'label': 'UPDATED', 'value': '2019-03-01T16:42:03Z'},
                         '85': {'label': 'REVISIONS', 'value': '17'},
                         '86': {'label': 'AGENCY', 'value': '1'},
                         '88': {'display': 'AVAILABLE',
                                'label': 'STATUS',
                                'value': '-'},
                         '93': {'label': 'INTL USE ', 'value': '0'},
                         '94': {'label': 'COPY USE', 'value': '0'},
                         '97': {'label': 'IMESSAGE', 'value': ' '},
                         '98': {'label': 'PDATE', 'value': '2019-02-27T20:13:09Z'}},
         'id': '16565480',
         'location': {'code': 'qhs', 'name': 'ANNEX HAY'},
         'status': {'code': '-', 'display': 'AVAILABLE'},
         'updatedDate': '2019-03-01T16:42:03Z',
         'varFields': [{'content': 'JH 153S ', 'fieldTag': 'b'},
                       {'content': 'Pleasure Readers (Greenleaf Classics)',
                        'fieldTag': 'p'},
                       {'content': 'Box 25', 'fieldTag': 'v'}]
        }
        self.assertEqual( 'no_callnumber_found', self.bib_info.build_callnumber(entry) )

        ## end def test_no_callnumber()

    def test_normal_callnumber(self):
        entry = {
         'barcode': '3 1236 07396 3426',
         'bibIds': ['5479552'],
         'callNumber': 'Ms.2010.043',
         'createdDate': '2011-04-19T20:58:33Z',
         'deleted': False,
         'fixedFields': {'108': {'label': 'OPACMSG', 'value': ' '},
              '109': {'label': 'Circ 7/2015+', 'value': '0'},
              '110': {'label': 'Circ 7/2013-6/2015', 'value': '0'},
              '127': {'label': 'AGENCY', 'value': '0'},
              '161': {'label': 'VI CENTRAL', 'value': '0'},
              '162': {'label': 'IR DIST LEARN SAME SITE', 'value': '0'},
              '264': {'label': 'Holdings Item Tag', 'value': '6'},
              '265': {'label': 'Inherit Location', 'value': 'false'},
              '57': {'label': 'BIB HOLD', 'value': 'false'},
              '58': {'label': 'COPY #', 'value': '1'},
              '59': {'label': 'ICODE1', 'value': '0'},
              '60': {'label': 'ICODE2', 'value': '-'},
              '61': {'display': 'Manuscript', 'label': 'I TYPE', 'value': '101'},
              '62': {'label': 'PRICE', 'value': '0.000000'},
              '64': {'label': 'OUT LOC', 'value': '0'},
              '70': {'label': 'IN LOC', 'value': '0'},
              '74': {'label': 'IUSE3', 'value': '0'},
              '76': {'label': 'Total Circ 1995+', 'value': '0'},
              '77': {'label': 'TOT RENEW', 'value': '0'},
              '79': {'display': 'ANNEX HAY', 'label': 'LOCATION', 'value': 'qhs'},
              '80': {'label': 'REC TYPE', 'value': 'i'},
              '81': {'label': 'RECORD #', 'value': '15990360'},
              '83': {'label': 'CREATED', 'value': '2011-04-19T20:58:33Z'},
              '84': {'label': 'UPDATED', 'value': '2019-07-31T13:00:24Z'},
              '85': {'label': 'REVISIONS', 'value': '5'},
              '86': {'label': 'AGENCY', 'value': '1'},
              '88': {'display': 'AVAILABLE', 'label': 'STATUS', 'value': '-'},
              '93': {'label': 'INTL USE ', 'value': '0'},
              '94': {'label': 'COPY USE', 'value': '0'},
              '97': {'label': 'IMESSAGE', 'value': ' '},
              '98': {'label': 'PDATE', 'value': '2014-09-04T21:04:00Z'}},
         'id': '15990360',
         'location': {'code': 'qhs', 'name': 'ANNEX HAY'},
         'status': {'code': '-', 'display': 'AVAILABLE'},
         'updatedDate': '2019-07-31T13:00:24Z',
         'varFields': [{'content': '3 1236 07396 3426', 'fieldTag': 'b'},
              {'content': 'Transferred from Hay Manuscripts to Annex Hay, AEG 4/22/2011',
               'fieldTag': 'n'},
              {'content': 'accessioned at Annex Hay 5/4/2011', 'fieldTag': 'n'},
              {'content': 'Box 2', 'fieldTag': 'v'}]
        }
        self.assertEqual( 'Ms.2010.043 Box 2', self.bib_info.build_callnumber(entry) )

        ## end def test_normal_callnumber()

    ## end class BibItemsTest


class EzbV1HelperTest( TestCase ):
    """ Checks helper functions. """

    def setUp(self):
        self.helper = EzbV1Helper()

    def test_oclc(self):
        self.assertEqual(
            {'validity': True, 'key': 'oclc', 'value': '21559548', 'error': None},
            self.helper.validate('oclc', '21559548') )

    def test_good_short_isbn(self):
        self.assertEqual(
            {'validity': True, 'key': 'isbn', 'value': '9780688002305', 'error': None},
            self.helper.validate('isbn', '0688002307') )

    def test_good_long_isbn(self):
        self.assertEqual(
            {'validity': True, 'key': 'isbn', 'value': '9780688002305', 'error': None},
            self.helper.validate('isbn', '9780688002305') )

    def test_bad_isbn(self):
        self.assertEqual(
            {'validity': False, 'key': 'isbn', 'value': '123', 'error': 'bad isbn'},
            self.helper.validate('isbn', '123') )

    def test_bad_key(self):
        self.assertEqual(
            {'validity': False, 'key': 'foo', 'value': 'bar', 'error': 'bad query-key'},
            self.helper.validate('foo', 'bar') )

    ## end EzbV1HelperTest()


class ISBNvalidatorTest( TestCase ):
    """ Checks submitted isbn. """

    def setUp(self):
        self.validator = Validator()

    def test_good_short_isbn(self):
        isbn = '0688002307'
        self.assertEqual( True, self.validator.validate_isbn(isbn) )
        self.assertEqual( '9780688002305', self.validator.EAN13 )

    def test_good_long_isbn(self):
        isbn = '9780688002305'
        self.assertEqual( True, self.validator.validate_isbn(isbn) )
        self.assertEqual( '9780688002305', self.validator.EAN13 )

    def test_bad_isbn(self):
        isbn = '123'
        self.assertEqual( False, self.validator.validate_isbn(isbn) )
        self.assertEqual( None, self.validator.EAN13 )

    def test_problematic_isbn(self):
        isbn = '0415232015(cased)'
        self.assertEqual( True, self.validator.validate_isbn(isbn) )
        self.assertEqual( '9780415232012', self.validator.EAN13 )

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
        response_dct = json.loads( response.content )
        self.assertEqual( 200, response.status_code )  # permanent redirect
        self.assertTrue(  b'time' in response.content )
        self.assertEqual( ['documentation', 'elapsed_time', 'version'], sorted(list(response_dct['response'].keys())) )

    def test_locations_and_statuses(self):
        """ Checks '/availability_api/locations_and_statuses/' """
        response = self.client.get( '/locations_and_statuses/' )  # project root part of url is assumed
        response_dct = json.loads( response.content )
        self.assertEqual( 200, response.status_code )  # permanent redirect
        self.assertTrue(  b'time' in response.content )
        self.assertEqual( ['ezb_available_locations', 'ezb_available_statuses', 'time_taken'], sorted(list(response_dct['response'].keys())) )

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

    def test_other_holdings_isbn(self):
        """ Checks `ezb_other_holdings` part of `basics` response. """
        expected = {
            'callNumber': 'WW Z2 M99w Suppl. ',
            'localLocation': 'HAY HARRIS',
            'publicNote': 'USE IN LIBRARY',
            'title': 'Supplement to "Walt Whitman, a descriptive bibliography" /',
            'url': 'https://search.library.brown.edu/catalog/b5707094' }
        response = self.client.get( '/v1/isbn/9781587299803/' )  # hay-harris Walt Whitman holding
        jdct = json.loads( response.content )
        result = jdct['response']['basics']['ezb_other_holdings'][0]
        self.assertEqual( expected, result )

    # def test_invalid_key(self):
    #     """ Checks non 'isbn' or 'oclc' key. """
    #     response = self.client.get( '/v2/foo/{}/'.format( settings_app.TEST_ISBN_FOUND_01) )  # project root part of url is assumed
    #     response_dct = json.loads( response.content )
    #     self.assertEqual( 'query_key bad', response_dct['response']['error'] )

    ## end class V1_UrlTest()


class ClientBibItemsTest( TestCase ):
    """ Checks isbn urls. """

    def test_response_bib(self):
        """ Checks for expected keys in response'. """
        response = self.client.get( '/v2/bib_items/b5479552/' )  # Diane Middlebrook papers
        content = response.content.decode('utf-8')
        rspns_dct = json.loads( content )
        self.assertEqual( 'the-title', rspns_dct['response']['bib']['title'] )
        self.assertEqual( 'the-author', rspns_dct['response']['bib']['author'] )

    ## end class ClientBibItemsTest()
