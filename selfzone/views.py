from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.views.decorators.cache import cache_control
from django.contrib.auth.decorators import login_required
from graphos.renderers import gchart
from graphos.renderers.highcharts import LineChart
from graphos.sources.simple import SimpleDataSource
from graphos.renderers import gchart

from django.db.models import Sum
from models import SelfieForm, Selfie, Match, History
from django.contrib.auth.models import User
from random import randint
from numpy.random import choice
from django.db.models import Count
from django.utils import timezone
import itertools


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def index(request):
    context = {}
    context['s1'], context['s2'] = select_selfies()
    return render(request, 'selfzone/index.html', context)


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def index_voted(request, old1_id, old2_id, voted):
    context = {}
    context["old1"] = get_object_or_404(Selfie, pk=old1_id)
    context["old2"] = get_object_or_404(Selfie, pk=old2_id)
    context["voted"] = voted
    context['s1'], context['s2'] = select_selfies()
    return render(request, 'selfzone/index.html', context)


def select_selfies():
    withtags = Selfie.objects.exclude(tags=None)
    # first selfie is random
    s1 = withtags.all()[randint(0, withtags.count()-1)]

    # select selfies with same (or less) number of faces (minimun 5 selfies)
    tries = 0
    f = Selfie.objects.exclude(id=s1.id).filter(faces=s1.faces)
    while f.count() <= 5:
        tries += 1
        f = Selfie.objects.exclude(id=s1.id).filter(faces=s1.faces-tries)

    # start filtring by tags (random weighted by priority)
    limit = int(f.count()*5/100 + 5) # minimum: 5%
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
    # selects from filtred selfie (random weighted by delta score and number of taken match)
    # filtred selfies are randomic limited
    weights = []
    selected = choice(f.all(), min(limit, f.count()), replace=False)
    print "selected selfies: ", len(selected)
    for s in selected:
        matches = s.lost_match_set.filter(winner=s1).count() + s.won_match_set.filter(loser=s1).count() + 1.0
        delta_score = float(abs(s.score-s1.score))
        weights.append(delta_score*matches)

    if sum(weights) != 0:
        weights = [max(weights)-i for i in weights]
        weights = [i/sum(weights) for i in weights]
        s2 = choice(selected, 1, p=weights)[0]
    else:
        s2 = selected[randint(0, len(selected)-1)]
    print "chosen: ", s2, "delta score: ", abs(s1.score-s2.score),
    print "matches: ", s2.lost_match_set.filter(winner=s1).count() + s2.won_match_set.filter(loser=s1).count()
    return s1, s2


@login_required
def upload(request):
    if request.method == 'POST':
        form = SelfieForm(request.POST, request.FILES)
        if form.is_valid():
            instance = Selfie(photo=request.FILES['photo'])
            instance.user = request.user
            instance.info = form.cleaned_data["info"]
            instance.save()
            print "new salfie: ", instance, "; anlisys result: ", instance.analyze()
            return HttpResponse('Successful update')
        return HttpResponse('Data Not Valid')
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

    m = Match.objects.create(winner=winner, loser=loser)
    winner.win_against(loser, m.match_date)

    # return HttpResponse("Won " + str(sW.id) + ": " + str(sW.won) + "/" + str(sW.loss) + "\n" +
    #                    "Lost " + str(sL.id) + ": " + str(sL.won) + "/" + str(sL.loss) + "\n")
    return HttpResponseRedirect(reverse('selfzone:index_voted', args=(s1.id, s2.id, voted)))


def details(request, selfie_id):
    selfie = get_object_or_404(Selfie, pk=selfie_id)
    pos = Selfie.objects.filter(score__gt=selfie.score).count() +1

    matches = (selfie.lost_match_set.all() | selfie.won_match_set.all())
    lasts = []
    for m in matches.order_by("match_date")[:10]:
        s = None
        color = None
        if m.winner.id == selfie.id:
            s = m.loser
            color = "green"
        else:
            s = m.winner
            color = "red"
        lasts.append({"selfie": s, "color": color})

    # scores per day
    days = [timezone.now().date() - timezone.timedelta(days=i) for i in range(60)]
    days = days[::-1]

    hist = History.objects.filter(selfie=s)
    scores = [hist.filter(date=d)[0].score if hist.filter(date=d).exists() else 1500.0 for d in days]

    data = [("day", "score")]
    for i in range(len(days)):
        data.append((days[i].strftime("%Y-%m-%d"), scores[i]))
    chart = AreaChart(SimpleDataSource(data=data), options={'title': "win vs loss"}, width="100%")

    nightmare = easy = None
    lost_with = selfie.lost_match_set.order_by("winner")
    if lost_with.count() > 0:
        grouped = itertools.groupby(lost_with, lambda r: r.winner)
        nightmare = sorted([(s, len(list(count))) for s, count in grouped], lambda x,y: cmp(y[1], x[1]))[0][0]

    win_with = selfie.won_match_set.order_by("loser")
    if win_with.count() > 0:
        grouped = itertools.groupby(win_with, lambda r: r.loser)
        easy = sorted([(s, len(list(count))) for s, count in grouped], lambda x,y: cmp(y[1], x[1]))[0][0]

    context = {'selfie': selfie, 'pos': pos, 'lasts': lasts, 'chart': chart, 'nightmare': nightmare, 'easy': easy}
    return render(request, 'selfzone/details.html', context)


class AreaChart(gchart.LineChart):
    def get_template(self):
        return "graphos/gchart/area_chart.html"


def stats(request):
    context = {}
    day = History.objects.filter(date=timezone.now().date()).order_by("-score").all()

    context['allTimeBest']  = Selfie.objects.all().order_by("-score").all()[:3]
    context['allTimeWorst'] = Selfie.objects.all().order_by("score").all()[:3]

    context['todayBest']  = [h.selfie for h in History.objects.filter(date=timezone.now().date()).order_by("-score").all()[:3]]
    context['todayWorst'] = [h.selfie for h in History.objects.filter(date=timezone.now().date()).order_by("score").all()[:3]]

    week = History.objects.filter(date__gte=timezone.now().date() - timezone.timedelta(timezone.now().weekday()))
    weekSum = week.values("selfie").annotate(totscore=Sum("score"))

    context['weekBest']  = [ Selfie.objects.get(pk=h["selfie"]) for h in weekSum.order_by("-totscore").all()[:3]]
    context['weekWorst'] = [ Selfie.objects.get(pk=h["selfie"]) for h in weekSum.order_by("totscore").all()[:3]]

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