import os

from django.core.files import File
from django.test import TestCase
from selfzone.views import select_selfies
import urllib
from selfzone.models import *


# Create your tests here.
class SelfieMethodTests(TestCase):

    def test_unrecognized(self):
        user = User.objects.create_user('test', password='test')

        s1 = Selfie.objects.create(user=user)
        s2 = Selfie.objects.create(user=user)
        self.assertEquals(Selfie.get_unrecognized().count(), 2)

        s2.faces = 1
        s2.save()
        self.assertEquals(Selfie.get_unrecognized().count(), 1)

    def init_selfie(self):
        Tag.init_tags()
        maleT = Tag.objects.get(tag="male")
        femaleT = Tag.objects.get(tag="female")
        user = User.objects.create_user('test', password='test')

        s1, s2 = select_selfies()
        self.assertEquals(s1, None)
        self.assertEquals(s2, None)
        s1 = Selfie.objects.create(user=user, faces=1)
        s1.tags.add(maleT)
        s1.save()
        s2 = Selfie.objects.create(user=user, faces=1)
        s2.tags.add(femaleT)
        s2.save()

    def test_select(self):
        self.init_selfie()

        s1, s2 = select_selfies()
        self.assertNotEqual(s1, None)
        self.assertNotEqual(s2, None)

    def test_match(self):
        self.init_selfie()
        s1, s2 = select_selfies()

        first_date = timezone.now() - timezone.timedelta(days=1)
        m = Match.objects.create(winner=s1, loser=s2, match_date=first_date)
        s1.win_against(s2, m.match_date)
        self.assertEquals(s1.score, 1501.0)
        self.assertEquals(s2.score, 1499.0)

        m = Match.objects.create(winner=s1, loser=s2, match_date=timezone.now())
        s1.win_against(s2, m.match_date)
        self.assertEquals(s1.score, 1501.5)
        self.assertEquals(s2.score, 1498.5)
        self.assertEquals(History.objects.count(), 4)
        self.assertEquals(s1.pub_date, first_date)

        self.assertEquals(s1.get_position(), 1)
        self.assertEquals(s1.first_day_score().score, 1501.0)

    def test_tag(self):
        self.init_selfie()
        self.assertEquals(Selfie.get_tagged("male").count(), 1)

    def test_details(self):
        self.init_selfie()

        s = Selfie.objects.all()[0]
        urllib.urlretrieve("http://blog.oxforddictionaries.com/wp-content/uploads/selfie4.jpg", "photo.jpg")
        s.photo = File(open("photo.jpg"))
        s.save()
        page = self.client.get("/selfzone/details/"+str(s.id))
        self.assertEquals(str(page).find("this selfie is not approved yet") < 0, True)

        Tag.objects.filter(selfie=s).delete()
        s.faces = 0
        s.save()
        page = self.client.get("/selfzone/details/"+str(s.id))
        self.assertEquals(str(page).find("this selfie is not approved yet") >= 0, True)

        os.remove("photo.jpg")