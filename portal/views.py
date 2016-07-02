from django.shortcuts import render

# Create your views here.
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from selfzone.models import Selfie, Match


@login_required
def portal_welcome(request):
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
        print wp

    context["selfies"] = selfies
    return render(request, 'portal/index.html', context)

