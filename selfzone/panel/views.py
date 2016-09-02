from django.db.models import Sum
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from selfzone.models import Selfie, Match, History
from django.contrib.auth import logout
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
import itertools

@login_required
def index(request):
    """
    If users are authenticated, direct them to the main page. Otherwise,
    take them to the login page.
    """
    return index_ordered(request, "score")


def index_ordered(request, type):

    if request.method == 'GET':
        list = Selfie.objects.filter(user=request.user)
        if type == "older":
            list = list.order_by("pub_date")
        if type == "newer":
            list = list.order_by("-pub_date")
        elif type == "score":
            list = list.order_by("-score")

        context = {'request': request}
        selfies = []
        for s in list.all():
            if s.won + s.loss == 0:
                wp = 50
            else:
                wp = float(s.won) * 100 / float(s.won + s.loss)
            selfies.append({"s": s, "w": wp, "imt": s.improving_tax()})

        context["selfies"] = selfies
        if len(selfies) == 0:
            return render(request, 'selfzone/panel/index.html', context)

        context["max_imt"] = max(selfies, key=lambda x: x["imt"])
        context["min_imt"] = min(selfies, key=lambda x: x["imt"])

        # verbose but optimized
        min_score = max_score = None
        for s in list:
            score = s.first_day_score()
            if score is None:
                continue
            if min_score is None or score.score < min_score.score:
                min_score = score
            if max_score is None or score.score > max_score.score:
                max_score = score

        context["max_first"] = max_score
        context["min_first"] = min_score

        day = History.objects.filter(date=timezone.now().date(), selfie__in=list)
        context['today_best'] = day.order_by("-score").all()[0]
        context['today_worst'] = day.order_by("score").all()[0]

        week = History.objects.filter(
            date__gte=timezone.now().date() - timezone.timedelta(timezone.now().weekday()),
            selfie__in=list)
        weeksum = week.values("selfie").annotate(totscore=Sum("score"))
        context['week_best'] = Selfie.objects.get(pk=weeksum.order_by("-totscore").all()[0]["selfie"])
        context['week_worst'] = Selfie.objects.get(pk=weeksum.order_by("totscore").all()[0]["selfie"])

        return render(request, 'selfzone/panel/index.html', context)

    else:
        type = "score"
        if request.POST["menu"] == "0":
            type = "score"
        elif request.POST["menu"] == "1":
            type = "older"
        elif request.POST["menu"] == "2":
            type = "newer"

        return HttpResponseRedirect(reverse('selfzone.panel:index_ordered', args=(type,)))


def logout_view(request):
    "Log users out and re-direct them to the main page."
    logout(request)
    return HttpResponseRedirect(reverse('selfzone:index'))


def register_ok(request):
    return render(request, 'selfzone/panel/register_ok.html')
