"""Hospitals — Django Admin Configuration"""

from django.contrib import admin

from hospitals.models import Hospital


@admin.register(Hospital)
class HospitalAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'created_at')
    search_fields = ('name',)
