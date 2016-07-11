from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from selfzone.models import Selfie, Match
from django.contrib.auth import logout
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse


@login_required
def index(request):
    """
    If users are authenticated, direct them to the main page. Otherwise,
    take them to the login page.
    """
    context = {'request': request}
    selfies = []
    for s in Selfie.objects.filter(user=request.user).all():
        if s.won + s.loss == 0:
            wp = 50
        else:
            wp = float(s.won)*100/float(s.won+s.loss)
        selfies.append({"s": s, "w": wp})

    context["selfies"] = selfies
    return render(request, 'selfzone/panel/index.html', context)


def logout_view(request):
    "Log users out and re-direct them to the main page."
    logout(request)
    return HttpResponseRedirect(reverse('selfzone:index'))