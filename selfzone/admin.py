from django.contrib import admin
from .models import Selfie


# Register your models here.
class SelfieAdmin(admin.ModelAdmin):
    list_filter = ('pub_date', 'tags')
    list_display = ('id', 'user', 'score', 'pub_date', 'analyzed')
    ordering = ('-pub_date',)
    search_fields = ['info']


admin.site.register(Selfie, SelfieAdmin)
