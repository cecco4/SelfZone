from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.views.decorators.cache import cache_control
from django.contrib.auth.decorators import login_required
from graphos.renderers import gchart
from graphos.renderers.highcharts import LineChart
from graphos.sources.simple import SimpleDataSource

from models import SelfieForm, Selfie, Match
from django.contrib.auth.models import User
from random import randint
from numpy.random import choice
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

    # select selfies with same (or less) number of faces
    tries = 0
    f = Selfie.objects.exclude(id=s1.id).filter(faces=s1.faces)
    while f.count() <= 1:
        tries += 1
        f = Selfie.objects.exclude(id=s1.id).filter(faces=s1.faces-tries)

    # start filtring by tags (random weighted by priority)
    limit = f.count()*5/100 + 5
    print "Start search from ", f.count(), limit

    tag_weights = [float(i.priority)+1 for i in s1.tags.all()]
    tag_weights = [i/sum(tag_weights) for i in tag_weights]
    for t in choice(s1.tags.all(), s1.tags.count(), replace=False, p=tag_weights):
        old = f
        f = f.filter(tags__tag=t.tag)
        print "("+t.tag+")down to ", f.count(),
        if f.count() < limit:   # keep only if have at least limit elements
            f = old
            continue

    print "selected selfies: ", f.count()
    # selects from filtred selfie (random weighted by delta score and number of taken match)
    weights = []
    for s in f.all():
        matches = s.loser_set.filter(winner=s1).count() + s.winner_set.filter(loser=s1).count() + 1
        delta_score = float(abs(s.score-s1.score)) + 1
        weights.append(delta_score*matches)
    weights = [max(weights)-i for i in weights]
    weights = [i/sum(weights) for i in weights]

    s2 = choice(f.all(), 1, p=weights)[0]
    print "chosen: ", s2, "delta score: ", abs(s1.score-s2.score),
    print "matches: ", s2.loser_set.filter(winner=s1).count() + s2.winner_set.filter(loser=s1).count()
    print "s1 expected:", Selfie.expected(s2.score, s1.score), "s2 expected:", Selfie.expected(s1.score, s2.score)
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

    Match.objects.create(winner=winner, loser=loser)
    winner.win_against(loser)

    # return HttpResponse("Won " + str(sW.id) + ": " + str(sW.won) + "/" + str(sW.loss) + "\n" +
    #                    "Lost " + str(sL.id) + ": " + str(sL.won) + "/" + str(sL.loss) + "\n")
    return HttpResponseRedirect(reverse('selfzone:index_voted', args=(s1.id, s2.id, voted)))


def details(request, selfie_id):
    selfie = get_object_or_404(Selfie, pk=selfie_id)
    matches = (selfie.loser_set.all() | selfie.winner_set.all())
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

    #matches per day
    g1 = group_by_day(selfie.winner_set, 14)
    g2 = group_by_day(selfie.loser_set, 14)

    data = [("day", "win", "loss")]
    for i in range(len(g1)):
        data.append((g1[i][0], g1[i][1], g2[i][1]))
    chart = AreaChart(SimpleDataSource(data=data), options={'title': "win vs loss"}, width="100%")
    return render(request, 'selfzone/details.html', {'selfie': selfie, 'lasts': lasts, 'chart': chart})


def group_by_day(set, days):
    last_days = timezone.now() - timezone.timedelta(days)
    m = set.filter(match_date__gte=last_days)
    grouped = itertools.groupby(m, lambda record: record.match_date.strftime("%Y-%m-%d"))
    matches_by_day = [(day, len(list(m_this_day))) for day, m_this_day in grouped]

    all_days = [t.strftime("%Y-%m-%d") for t in [timezone.now() - timezone.timedelta(i) for i in range(days)]]
    mat_days = [d for d, c in matches_by_day]
    for d in all_days:
        if d not in mat_days:
            matches_by_day.append((d, 0))
    return sorted(matches_by_day, lambda x, y: cmp(x[0], y[0]))

from graphos.renderers import gchart

class AreaChart(gchart.LineChart):
    def get_template(self):
        return "graphos/gchart/area_chart.html"