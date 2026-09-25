"""Customise the Django Admin site header & titles for MoneXa."""
from django.contrib import admin

admin.site.site_header = "MoneXa — Back-office"
admin.site.site_title = "MoneXa Admin"
admin.site.index_title = "Tableau de bord"
