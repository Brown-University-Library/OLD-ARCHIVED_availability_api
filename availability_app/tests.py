# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import logging
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

    # end class UrlTest()


class IsbnTest( TestCase ):
    """ Checks isbn urls. """

    def test_found_isbn_1(self):
        """ Checks found isbn'. """
        response = self.client.get( '/v2/isbn/{}/'.format( settings_app.TEST_ISBN_FOUND_01) )  # project root part of url is assumed
        content = response.content.decode('utf-8')
        self.assertTrue( '"bibid": ".b18151139"' in content )
        self.assertTrue( '"bibid": ".b27679275"' in content )
        self.assertTrue( 'Zen and the art of motorcycle maintenance' in content )

    def test_found_isbn_2(self):
        """ Checks found isbn that was problematic in old api'. """
        response = self.client.get( '/v2/isbn/{}/'.format( settings_app.TEST_ISBN_FOUND_02) )  # project root part of url is assumed
        content = response.content.decode('utf-8')
        self.assertTrue( 'foo' in content )


    # end class IsbnTest
