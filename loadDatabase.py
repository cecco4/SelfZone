from selfzone.models import Selfie
from django.contrib.auth.models import User
import os
from django.core.files import File


path = "/home/cecco/Documenti/django-projects/InstaDownloader/pics/"
for pic in os.listdir(path):
    user = User.objects.all()[0]
    s = Selfie()
    s.user = user
    s.photo = File(open(os.path.join(os.path.abspath(path), pic)))
    s.save()
    s.analyze()
    print "new selfie: ", pic
