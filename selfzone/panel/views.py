from django.shortcuts import render
from django.contrib.auth.decorators import login_required
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