from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.views.decorators.cache import cache_control
from django.contrib.auth.decorators import login_required
from graphos.renderers import gchart
from graphos.renderers.highcharts import LineChart
from graphos.sources.simple import SimpleDataSource
from graphos.renderers import gchart
from django.views.decorators.csrf import csrf_exempt

from isoweek import Week
from django.db.models import Sum
from models import SelfieForm, Selfie, Match, History
from django.contrib.auth.models import User
from random import randint
from numpy.random import choice
from django.db.models import Count
from django.utils import timezone
import itertools
from PIL import Image


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def index(request):
    context = {}
    context['s1'], context['s2'] = select_selfies()
    return render(request, 'selfzone/index.html', context)


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def index_voted(request, old1_id, old2_id, voted):
    context = {}
    old1 = get_object_or_404(Selfie, pk=old1_id)
    old2 = get_object_or_404(Selfie, pk=old2_id)

    agree = 50.0
    old1_w = old1.won_match_set.filter(loser=old2).count()
    old2_w = old2.won_match_set.filter(loser=old1).count()

    print "wins: ", old1_w, old2_w
    if voted == "left":
        agree = old1_w*100.0 / (old1_w + old2_w)
    elif voted == "right":
        agree = old2_w*100.0 / (old1_w + old2_w)

    context["old1"] = old1
    context["old2"] = old2
    context["voted"] = voted
    context["agree"] = int(agree)
    context['s1'], context['s2'] = select_selfies()
    return render(request, 'selfzone/index.html', context)


def select_selfies():
    withtags = Selfie.objects.exclude(tags=None)
    if withtags.count() == 0:
        return None, None

    # first selfie is random
    s1 = withtags.all()[randint(0, withtags.count()-1)]

    if withtags.count() == 1:
        return s1, None

    # select selfies with same (or less) number of faces (minimun 5 selfies)
    tries = 0
    f = Selfie.objects.exclude(id=s1.id).filter(faces=s1.faces)
    while f.count() <= 5:
        tries += 1
        f = Selfie.objects.exclude(id=s1.id).filter(faces__gte=s1.faces-tries, faces__lte=s1.faces)
        if tries > 10:
            f = Selfie.objects.exclude(id=s1.id)
            return s1, f.all()[randint(0, f.count()-1)]

    # start filtring by tags (random weighted by priority)
    limit = int(f.count()*5/100 + 5)  # minimum: 5%
    print "Start search from ", f.count(), limit

    tag_weights = [float(i.priority)+1 for i in s1.tags.all()]
    tag_weights = [i/sum(tag_weights) for i in tag_weights]
    max_tags = 3

    old = f
    minimum = limit / 4
    while True:
        for t in choice(s1.tags.all(), max_tags, replace=False, p=tag_weights):
            print "filter", t.tag
            f = f.filter(tags__tag=t.tag)
        if f.count() >= minimum:
            break
        else:
            print f.count(), "discard"
            f = old
            minimum /= 2

    if f.count() == 1:
        return s1, f.all()[0]
    elif f.count() < 1:
        return s1, withtags.all()[randint(0, withtags.count()-1)]

    # selects from filtred selfie (random weighted by delta score and number of taken match)
    # filtred selfies are randomic limited
    weights = []
    selected = choice(f.all(), min(limit, f.count()), replace=False)
    print "selected selfies: ", len(selected)
    for s in selected:
        matches = s.lost_match_set.filter(winner=s1).count() + s.won_match_set.filter(loser=s1).count() + 1.0
        delta_score = float(abs(s.score-s1.score))
        weights.append(delta_score*matches)

    weights = [max(weights) - i for i in weights]
    if sum(weights) != 0:
        weights = [i/sum(weights) for i in weights]
        s2 = choice(selected, 1, p=weights)[0]
    else:
        s2 = selected[randint(0, len(selected)-1)]
    print "chosen: ", s2, "delta score: ", abs(s1.score-s2.score),
    print "matches: ", s2.lost_match_set.filter(winner=s1).count() + s2.won_match_set.filter(loser=s1).count()
    return s1, s2


@login_required
@csrf_exempt
def upload(request):
    if request.method == 'POST':
        form = SelfieForm(request.POST, request.FILES)
        if form.is_valid():
            instance = Selfie(photo=request.FILES['photo'])
            instance.user = request.user
            instance.info = form.cleaned_data["info"]
            instance.save()

            hist = History(selfie=instance, date=instance.pub_date, matches=0, score=1500)
            hist.save()

            img = Image.open(instance.photo.file)
            x1 = float(request.POST["x1"])
            x2 = float(request.POST["x2"])
            y1 = float(request.POST["y1"])
            y2 = float(request.POST["y2"])
            img.crop((x1, y1, x2, y2)).resize((640, 640)).save(instance.photo.file.file.name)

            print "new salfie: ", instance, "; anlisys result: ", instance.analyze()
            return HttpResponseRedirect(reverse('selfzone.panel:index'))
        return render(request, 'selfzone/uploadForm.html', {'form': form})
    else:
        form = SelfieForm()
        return render(request, 'selfzone/uploadForm.html', {'form': form})


def vote(request, s1_id, s2_id, voted):
    s1 = get_object_or_404(Selfie, pk=s1_id)
    s2 = get_object_or_404(Selfie, pk=s2_id)
    winner = loser = None
    if voted == "left":
        winner = s1
        loser = s2
    elif voted == "right":
        winner = s2
        loser = s1

    m = Match.objects.create(winner=winner, loser=loser, match_date=timezone.now())
    winner.win_against(loser, m.match_date)
    # return HttpResponse("Won " + str(sW.id) + ": " + str(sW.won) + "/" + str(sW.loss) + "\n" +
    #                    "Lost " + str(sL.id) + ": " + str(sL.won) + "/" + str(sL.loss) + "\n")
    return HttpResponseRedirect(reverse('selfzone:index_voted', args=(s1.id, s2.id, voted)))


def details(request, selfie_id):
    selfie = get_object_or_404(Selfie, pk=selfie_id)
    pos = selfie.get_position()

    matches = (selfie.lost_match_set.all() | selfie.won_match_set.all())
    lasts = []
    for m in matches.order_by("-match_date")[:10]:
        s = None
        color = None
        if m.winner.id == selfie.id:
            s = m.loser
            color = "green"
        else:
            s = m.winner
            color = "red"
        lasts.append({"selfie": s, "color": color})

    # scores graph for last 15 days
    days = [timezone.now().date() - timezone.timedelta(days=i) for i in range(15)]
    score = selfie.score
    scores = []
    allmatch = matches.order_by("match_date")
    i = allmatch.count() -1
    for d in days:
        scores.append(score)
        day = timezone.datetime(d.year, d.month, d.day)
        # calculation is reversed for performance
        while i >= 0 and allmatch.all()[i].match_date > day:
            value = 1.0/(i+1)
            if allmatch.all()[i].winner == selfie:
                value = -value
            score += value
            i -= 1

    data = [("day", "score")]
    for i in reversed(range(len(days))):
        data.append((days[i].strftime("%Y-%m-%d"), scores[i]))
    chart = AreaChart(SimpleDataSource(data=data), options={'title': "win vs loss"}, width="100%")

    nightmare = easy = None
    lost_with = selfie.lost_match_set.order_by("winner")
    if lost_with.count() > 0:
        grouped = itertools.groupby(lost_with, lambda r: r.winner)
        nightmare = sorted([(s, len(list(count))) for s, count in grouped], lambda x,y: cmp(y[1], x[1]))[0]

    win_with = selfie.won_match_set.order_by("loser")
    if win_with.count() > 0:
        grouped = itertools.groupby(win_with, lambda r: r.loser)
        easy = sorted([(s, len(list(count))) for s, count in grouped], lambda x,y: cmp(y[1], x[1]))[0]

    context = {'selfie': selfie, 'pos': pos, 'lasts': lasts, 'chart': chart, 'nightmare': nightmare, 'easy': easy}
    return render(request, 'selfzone/details.html', context)


class AreaChart(gchart.LineChart):
    def get_template(self):
        return "graphos/gchart/area_chart.html"


class PieChart(gchart.PieChart):
    def get_template(self):
        return "graphos/gchart/pie_chart.html"

def stats(request):
    context = {}

    # TODO: finish statistics
    # get numbers
    context["tot_selfie"] = Selfie.objects.count() - Selfie.get_unrecognized().count()
    context["tot_matches"] = Match.objects.count()

    male        = Selfie.get_tagged("male").count()
    female      = Selfie.get_tagged("female").count()
    young       = Selfie.get_tagged("young").count()
    old         = Selfie.get_tagged("old").count()
    baby        = Selfie.get_tagged("baby").count()
    neutral     = Selfie.get_tagged("neutral").count()
    sad         = Selfie.get_tagged("sad").count()
    anger       = Selfie.get_tagged("anger").count()
    happiness   = Selfie.get_tagged("happiness").count()
    surprise    = Selfie.get_tagged("surprise").count()

    data = [("gender", "percentage"), ("male", male), ("female", female)]
    chart = PieChart(SimpleDataSource(data=data), width="100%")
    context['gender_chart'] = chart

    data = [("age", "percentage"), ("baby", baby), ("young", young), ("old", old)]
    chart = PieChart(SimpleDataSource(data=data), width="100%")
    context['age_chart'] = chart

    data = [("face expression", "percentage"), ("neutral", neutral), ("sad", sad),
            ("anger", anger), ("happiness", happiness), ("surprise", surprise)]
    chart = PieChart(SimpleDataSource(data=data), width="100%")
    context['face_chart'] = chart

    context['allTimeBest']  = Selfie.objects.all().order_by("-score").all()[:3]
    context['allTimeWorst'] = reversed(Selfie.objects.all().order_by("score").all()[:3])

    day = History.objects.filter(date=timezone.now().date())
    context['todayBest']  = [h.selfie for h in day.order_by("-score").all()[:3]]
    context['todayWorst'] = reversed([h.selfie for h in day.order_by("score").all()[:3]])

    week = History.objects.filter(date__gte=timezone.now().date() - timezone.timedelta(timezone.now().weekday()))
    weeksum = week.values("selfie").annotate(totscore=Sum("score"))
    context['weekBest']  = [Selfie.objects.get(pk=h["selfie"]) for h in weeksum.order_by("-totscore").all()[:3]]
    context['weekWorst'] = reversed([Selfie.objects.get(pk=h["selfie"]) for h in weeksum.order_by("totscore").all()[:3]])

    context['day'] = timezone.now().day
    context['month'] = timezone.now().month
    context['year'] = timezone.now().year
    context['week'] = timezone.now().isocalendar()[1]
    return render(request, 'selfzone/stats.html', context)


def top(request, num):
    if num == "":
        num = 10
    list = Selfie.objects.order_by("-score").all()[:int(num)]
    return render(request, 'selfzone/top.html', {"list": list})


def bottom(request, num):
    if num == "":
        num = 10
    list = Selfie.objects.order_by("score").all()[:int(num)]
    return render(request, 'selfzone/top.html', {"list": list})


def top_day(request, year, month, day, num):
    if num == "":
        num = 10
    year = int(year)
    month = int(month)
    day = int(day)
    num = int(num)

    scores = History.objects.filter(date=timezone.datetime(year, month, day).date()).order_by("-score").all()[:num]
    list = [h.selfie for h in scores]
    return render(request, 'selfzone/top.html', {"list": list})


def bottom_day(request, year, month, day, num):
    if num == "":
        num = 10
    year = int(year)
    month = int(month)
    day = int(day)
    num = int(num)

    scores = History.objects.filter(date=timezone.datetime(year, month, day).date()).order_by("score").all()[:num]
    list = [h.selfie for h in scores]
    return render(request, 'selfzone/top.html', {"list": list})


def top_week(request, year, week, num):
    if num == "":
        num = 10
    year = int(year)
    week = int(week)
    num = int(num)

    week = History.objects.filter(date__gte=Week(year, week).monday(),
                                  date__lte=Week(year, week).friday())
    weeksum = week.values("selfie").annotate(totscore=Sum("score"))
    list = [Selfie.objects.get(pk=h["selfie"]) for h in weeksum.order_by("-totscore").all()[:num]]
    return render(request, 'selfzone/top.html', {"list": list})


def bottom_week(request, year, week, num):
    if num == "":
        num = 10
    year = int(year)
    week = int(week)
    num = int(num)

    week = History.objects.filter(date__gte=Week(year, week).monday(),
                                  date__lte=Week(year, week).friday())
    weeksum = week.values("selfie").annotate(totscore=Sum("score"))
    list = [Selfie.objects.get(pk=h["selfie"]) for h in weeksum.order_by("totscore").all()[:num]]
    return render(request, 'selfzone/top.html', {"list": list})