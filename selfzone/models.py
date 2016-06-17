from __future__ import unicode_literals
from django.utils import timezone

from django.db import models
from django.contrib.auth.models import User
from django import forms


# Create your models here.
class Selfie(models.Model):
    photo = models.FileField(upload_to = 'selfies/%Y/')
    user = models.ForeignKey(User)
    info = models.CharField(max_length=200, default="selfie pic")
    pub_date = models.DateTimeField('date published', default=timezone.now)
    won = models.IntegerField(default=0)
    loss = models.IntegerField(default=0)

    def __unicode__(self):
        return "Selfie"


class SelfieForm(forms.ModelForm):
    class Meta:
        model = Selfie
        fields = ['photo', 'info']