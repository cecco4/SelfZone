from django.contrib import admin
from .models import Selfie


# Register your models here.
class SelfieAdmin(admin.ModelAdmin):
    list_filter = ['pub_date', 'tags']

admin.site.register(Selfie, SelfieAdmin)
