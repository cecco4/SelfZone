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
    context["selfies"] = Selfie.objects.filter(user=request.user).all()
    print context["selfies"]
    return render(request, 'portal/index.html', context)

