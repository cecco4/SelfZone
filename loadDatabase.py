from selfzone.models import Selfie
from django.contrib.auth.models import User
import os
from django.core.files import File
from django.contrib.auth.models import User
from random import randint

#print "create some users"
#for i in range(0, 20):
#    user = User.objects.create_user('cecco'+str(i), password='cecco')
#    user.save()
#    print user

print "upload selfies"
path = "/home/cecco/Documenti/django-projects/InstaDownloader/pics/"
for pic in os.listdir(path):
    user = User.objects.all()[randint(0, len(User.objects.all())-1)]
    s = Selfie()
    s.user = user
    s.photo = File(open(os.path.join(os.path.abspath(path), pic)))
    s.save()
    s.analyze()
    print "new selfie: ", pic
