from __future__ import unicode_literals
from django.utils import timezone

from django.db import models
from django.contrib.auth.models import User
from django import forms
import angus
import sys


# Create your models here.
class Tag(models.Model):
    tag = models.CharField(max_length=128)
    priority = models.IntegerField(default=0)

    def __unicode__(self):
        return self.tag

    @staticmethod
    def init_tags():
        Tag.objects.update_or_create(tag="female",            defaults={"priority": 4})
        Tag.objects.update_or_create(tag="male",              defaults={"priority": 4})
        Tag.objects.update_or_create(tag="neutral",           defaults={"priority": 3})
        Tag.objects.update_or_create(tag="sad",               defaults={"priority": 3})
        Tag.objects.update_or_create(tag="anger",             defaults={"priority": 3})
        Tag.objects.update_or_create(tag="happiness",         defaults={"priority": 3})
        Tag.objects.update_or_create(tag="surprise",          defaults={"priority": 3})
        Tag.objects.update_or_create(tag="center",            defaults={"priority": 2})
        Tag.objects.update_or_create(tag="young",             defaults={"priority": 2})
        Tag.objects.update_or_create(tag="up",                defaults={"priority": 2})
        Tag.objects.update_or_create(tag="left",              defaults={"priority": 2})
        Tag.objects.update_or_create(tag="right",             defaults={"priority": 2})
        Tag.objects.update_or_create(tag="down",              defaults={"priority": 2})
        Tag.objects.update_or_create(tag="old",               defaults={"priority": 2})
        Tag.objects.update_or_create(tag="baby",              defaults={"priority": 2})
        Tag.objects.update_or_create(tag="head_zero",         defaults={"priority": 1})
        Tag.objects.update_or_create(tag="head_down",         defaults={"priority": 1})
        Tag.objects.update_or_create(tag="head_roll_left",    defaults={"priority": 1})
        Tag.objects.update_or_create(tag="head_left",         defaults={"priority": 1})
        Tag.objects.update_or_create(tag="head_roll_right",   defaults={"priority": 1})
        Tag.objects.update_or_create(tag="head_right",        defaults={"priority": 1})
        Tag.objects.update_or_create(tag="head_up",           defaults={"priority": 1})
        Tag.objects.update_or_create(tag="eye_down",          defaults={"priority": 0})
        Tag.objects.update_or_create(tag="eye_right",         defaults={"priority": 0})
        Tag.objects.update_or_create(tag="eye_left",          defaults={"priority": 0})
        Tag.objects.update_or_create(tag="eye_up",            defaults={"priority": 0})
        Tag.objects.update_or_create(tag="eye_zero",          defaults={"priority": 0})


class Selfie(models.Model):
    photo = models.ImageField(upload_to = 'selfies/%Y/')
    user = models.ForeignKey(User)
    info = models.CharField(max_length=200, default="")
    pub_date = models.DateTimeField('date published', default=timezone.now)
    won = models.IntegerField(default=0)
    loss = models.IntegerField(default=0)
    score = models.FloatField(default=1500.0)

    faces = models.IntegerField(default=0)
    tags = models.ManyToManyField(Tag)

    def __unicode__(self):
        return str(self.id)

    def analyze(self):
        services = ('age_and_gender_estimation', 'face_expression_estimation', 'gaze_analysis')
        url = "https://gate.angus.ai"
        c_id = "1269cac4-3537-11e6-819d-0242ac110002"
        a_tk = "b407f040-fca7-4dfa-80de-f7399deed597"
        conf = angus.get_default_configuration()
        conf.set_credential(client_id=c_id, access_token=a_tk)

        conn = angus.connect(url=url, conf=conf)
        s = conn.services.get_services(services)
        job = s.process({'image': open(self.photo.path)})
        res = job.result

        res_age_gender = res['age_and_gender_estimation']
        res_expr = res['face_expression_estimation']
        res_gaze = res['gaze_analysis']
        self.faces = int(res_age_gender['nb_faces'])

        tags = []
        for face in res_age_gender['faces']:
            tags.append(face['gender'])
            if   face['age'] < 10: tags.append("baby")
            elif face['age'] < 40: tags.append("young")
            else:                  tags.append("old")

            size = res_age_gender['input_size']
            roi = face['roi']
            center = [roi[0] + roi[2]/2, roi[1] + roi[3]/2]
            c = False
            if   center[0] < size[0]/2 - size[0]/10: tags.append("left")
            elif center[0] > size[0]/2 + size[0]/10: tags.append("right")
            else: c = True

            if   center[1] < size[1]/2 - size[1]/10: tags.append("up")
            elif center[1] > size[1]/2 + size[1]/10: tags.append("down")
            else: c = True

            if c:
                tags.append("center")

        for face in res_expr['faces']:
            if face['sadness']   > 0.5: tags.append("sad")
            if face['neutral']   > 0.5: tags.append("neutral")
            if face['anger']     > 0.5: tags.append("anger")
            if face['surprise']  > 0.5: tags.append("surprise")
            if face['happiness'] > 0.5: tags.append("happiness")

        for face in res_gaze['faces']:
            if   face['head_pitch'] < -0.2: tags.append("head_down")
            elif face['head_pitch'] >  0.2: tags.append("head_up")
            else:                           tags.append("head_zero")

            if   face['head_yaw'] < -0.2: tags.append("head_right")
            elif face['head_yaw'] >  0.2: tags.append("head_left")
            else:                         tags.append("head_zero")

            if   face['head_roll'] < -0.2: tags.append("head_roll_right")
            elif face['head_roll'] >  0.2: tags.append("head_roll_left")
            else:                          tags.append("head_zero")

            if   face['gaze_pitch'] < -0.2: tags.append("eye_down")
            elif face['gaze_pitch'] >  0.2: tags.append("eye_up")
            else:                           tags.append("eye_zero")

            if   face['gaze_yaw'] < -0.2: tags.append("eye_right")
            elif face['gaze_yaw'] >  0.2: tags.append("eye_left")
            else:                         tags.append("eye_zero")

        tags = set(tags)
        for t in tags:
            print "get", t
            tag = Tag.objects.get(tag=t)
            self.tags.add(tag)
        self.save()
        return self.faces

    @staticmethod
    def get_unrecognized():
        return Selfie.objects.filter(faces=0)

    @staticmethod
    def recalculate_all():
        print "delete history"
        tot = History.objects.count()
        for i in xrange(0, tot):
            History.objects.all()[0].delete()
            progress = (float(i)/tot)*100
            sys.stdout.write("\r%d%%" % progress)
            sys.stdout.flush()

        print "\nreinit selfie data"
        for i in xrange(0, Selfie.objects.count()):
            s = Selfie.objects.all()[i]
            s.won = 0
            s.loss = 0
            s.score = 1500.0
            s.save()
            progress = (float(i)/Selfie.objects.count())*100
            sys.stdout.write("\r%d%%" % progress)
            sys.stdout.flush()

        print "\ncalculate matches"
        tot = Match.objects.count()
        n = 0
        for m in Match.objects.order_by("match_date"):
            m.winner.win_against(m.loser, m.match_date)
            n+=1

            progress = (float(n) / tot) * 100
            sys.stdout.write("\r%d%%" % progress)
            sys.stdout.flush()

    def win_against(self, loser, date):
        self.won += 1
        loser.loss += 1

        w_score = self.score + 1.0/(self.won+self.loss)
        l_score = loser.score + 1.0/(loser.won+loser.loss)
        self.score = w_score
        loser.score = l_score

        self.save()
        loser.save()

        hist = History.objects.get_or_create(selfie=self, date=date.date())[0]
        hist.matches += 1
        hist.score += 1.0 / hist.matches
        hist.save()

        hist = History.objects.get_or_create(selfie=loser, date=date.date())[0]
        hist.matches += 1
        hist.score -= 1.0 / hist.matches
        hist.save()


class Match(models.Model):
    winner = models.ForeignKey(Selfie, related_name="won_match_set")
    loser = models.ForeignKey(Selfie, related_name="lost_match_set")
    match_date = models.DateTimeField(default=timezone.now)


class History(models.Model):
    selfie = models.ForeignKey(Selfie, related_name="history_set")
    score = models.FloatField(default=1500.0)
    matches = models.IntegerField(default=0)
    date = models.DateField(default=timezone.now)

    def won(self):
        start = self.date
        end = start + timezone.timedelta(days=1)
        return self.selfie.won_match_set.filter(match_date__gte=start, match_date__lte=end).count()

    def lost(self):
        start = self.date
        end = start + timezone.timedelta(days=1)
        return self.selfie.lost_match_set.filter(match_date__gte=start, match_date__lte=end).count()


class SelfieForm(forms.ModelForm):
    photo = forms.ImageField()
    info = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = Selfie
        fields = ['photo', 'info']