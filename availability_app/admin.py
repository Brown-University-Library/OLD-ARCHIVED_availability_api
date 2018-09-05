# -*- coding: utf-8 -*-

from .models import Tracker
from django.contrib import admin


class TrackerAdmin( admin.ModelAdmin ):
    list_display = [ 'count_date', 'ezb_isbn_count', 'ezb_bib_count', 'unofficial_access_count', 'dt_created', 'dt_modified' ]
    ordering = [ '-count_date' ]
    readonly_fields = [ 'count_date', 'ezb_isbn_count', 'ezb_bib_count', 'unofficial_access_count', 'dt_created', 'dt_modified' ]


admin.site.register( Tracker, TrackerAdmin )
