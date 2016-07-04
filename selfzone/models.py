from __future__ import unicode_literals
from django.utils import timezone

from django.db import models
from django.contrib.auth.models import User
from django import forms
import angus


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
    photo = models.FileField(upload_to = 'selfies/%Y/')
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
        print "reinit data to zero"
        for s in Selfie.objects.all():
            s.won = 0
            s.loss = 0
            s.score = 1500.0
            s.save()

        print "calculate matches"
        tot = str(Match.objects.count())
        n = 0
        for m in Match.objects.order_by("match_date"):
            n +=1
            print str(n)+"/"+tot, m.match_date,
            m.winner.win_against(m.loser)

    def win_against(self, loser):
        self.won += 1
        loser.loss += 1
        w_score = Selfie.win_score(self.score, Selfie.expected(loser.score, self.score))
        l_score = Selfie.loss_score(loser.score, Selfie.expected(self.score, loser.score))
        print "winner new:", self.score, "loser new:", loser.score
        self.score = w_score
        loser.score = l_score
        self.save()
        loser.save()

    @staticmethod
    def expected(score_b, score_a):
        return 1 / (1 + pow(10, (score_b - score_a) / 400))

    @staticmethod
    def win_score(score, expected):
        return score + 24 * (1 - expected)

    @staticmethod
    def loss_score(score, expected):
        return score + 24 * (0 - expected)


class Match(models.Model):
    winner = models.ForeignKey(Selfie, related_name="winner_set")
    loser = models.ForeignKey(Selfie, related_name="loser_set")
    match_date = models.DateTimeField(default=timezone.now)


class SelfieForm(forms.ModelForm):
    photo = forms.FileField()
    info = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = Selfie
        fields = ['photo', 'info']