# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import datetime, json, logging, os, pprint
from django.conf import settings as project_settings
from django.core.urlresolvers import reverse
from django.db import models
from django.http import HttpResponseRedirect

log = logging.getLogger(__name__)


class Tracker( models.Model ):
    count_date = models.DateField( blank=True, null=True )
    ezb_isbn_count = models.IntegerField( null=True, blank=True )
    ezb_oclc_count = models.IntegerField( null=True, blank=True )
    ezb_bib_count = models.IntegerField( null=True, blank=True )
    unofficial_access_count = models.IntegerField( null=True, blank=True )
    dt_created = models.DateTimeField( auto_now_add=True )
    dt_modified = models.DateTimeField( auto_now=True )
