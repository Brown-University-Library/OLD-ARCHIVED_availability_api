# -*- coding: utf-8 -*-

import os


DOCUMENTATION_URL = os.environ['AVL_API__DOCUMENTATIN_URL']


## for z39.50 lookups
Z_HOST = os.environ['AVL_API__Z_HOST']
Z_PORT = os.environ['AVL_API__Z_PORT']
Z_TYPE = os.environ['AVL_API__Z_TYPE']


## for tests
TEST_ISBN_FOUND_01 = os.environ['AVL_API__ISBN_FOUND_01']
TEST_ISBN_FOUND_02 = os.environ['AVL_API__ISBN_FOUND_02']
