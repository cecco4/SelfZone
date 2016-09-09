from django.db import models
from django.contrib import admin
from django.forms import CheckboxSelectMultiple
from selfzone.models import Selfie


# Register your models here.
class SelfieAdmin(admin.ModelAdmin):
    list_filter = ('pub_date', 'tags')
    list_display = ('id', 'user', 'score', 'pub_date', 'analyzed')
    ordering = ('-pub_date',)
    search_fields = ('info',)

    formfield_overrides = {
        models.ManyToManyField: {'widget': CheckboxSelectMultiple},
    }

    fieldsets = [
        ('Data info', {'fields': ['photo', 'info', 'user', 'pub_date']}),
        ('photo info', {'fields': ['faces', 'tags'], 'classes': ['collapse']}),
    ]

admin.site.register(Selfie, SelfieAdmin)
