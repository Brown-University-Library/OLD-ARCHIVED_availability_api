# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import json, logging, pprint
from availability_app import settings_app
from django.test import TestCase


log = logging.getLogger(__name__)
TestCase.maxDiff = None



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
        log.debug( 'response, ```%s```' % response )
        log.debug( 'response.content, ```%s```' % response.content )
        self.assertEqual( 200, response.status_code )  # permanent redirect
        self.assertTrue(  b'time' in response.content )

    # def test_invalid_key(self):
    #     """ Checks non 'isbn' or 'oclc' key. """
    #     response = self.client.get( '/v2/foo/{}/'.format( settings_app.TEST_ISBN_FOUND_01) )  # project root part of url is assumed
    #     response_dct = json.loads( response.content )
    #     self.assertEqual( 'query_key bad', response_dct['response']['error'] )

    # end class UrlTest()




# class V2_IsbnUrlTest( TestCase ):
#     """ Checks isbn urls. """

#     def test_found_isbn_1(self):
#         """ Checks found isbn'. """
#         response = self.client.get( '/v2/isbn/{}/'.format( settings_app.TEST_ISBN_FOUND_01) )  # project root part of url is assumed
#         content = response.content.decode('utf-8')
#         self.assertTrue( '"bibid": ".b18151139"' in content )
#         self.assertTrue( '"bibid": ".b27679275"' in content )
#         self.assertTrue( 'Zen and the art of motorcycle maintenance' in content )

#     def test_no_duplicate_bibs(self):
#         """ Checks handling when duplicate are returned by the z39.50 search. """
#         response = self.client.get( '/v2/isbn/{}/'.format( settings_app.TEST_ISBN_FOUND_02) )  # project root part of url is assumed
#         response_dct = json.loads( response.content )
#         bib_list = []
#         for entry in response_dct['response']['backend_response']:
#             log.debug( 'current bibid, `{}`'.format(entry['bibid']) )
#             self.assertEqual( False, entry['bibid'] in bib_list )
#             bib_list.append( entry['bibid'] )
#             log.debug( 'bib_list is now, ```{}```'.format(pprint.pformat(bib_list)) )

#     def test_found_isbn_2(self):
#         """ Checks found isbn that was problematic in old api'. """
#         response = self.client.get( '/v2/isbn/{}/'.format( settings_app.TEST_ISBN_FOUND_02) )  # project root part of url is assumed
#         content = response.content.decode('utf-8')
#         self.assertTrue( '"bibid": ".b28149300"' in content )
#         self.assertTrue( '"bibid": ".b26968939"' in content )
#         self.assertTrue( 'Africa and Africans' in content )
#         self.assertTrue( 'The Kongolese Saint Anthony' in content )

#     # end class V2_IsbnUrlTest
