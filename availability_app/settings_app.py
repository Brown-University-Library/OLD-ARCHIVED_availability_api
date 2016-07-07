# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import os


## for z39.50 lookups
Z_HOST = unicode( os.environ['AVL_API__Z_HOST'] )
Z_PORT = unicode( os.environ['AVL_API__Z_PORT'] )
Z_TYPE = unicode( os.environ['AVL_API__Z_TYPE'] )
