from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from models import SelfieForm, Selfie
from django.contrib.auth.models import User
from random import randint


def index(request):
    context = {}

    n = len(Selfie.objects.all()) - 1
    context["s1"] = Selfie.objects.all()[randint(0, n)]
    context["s2"] = Selfie.objects.all()[randint(0, n)]

    context["s1"].analyze()
    return render(request, 'selfzone/index.html', context)


def index_voted(request, old1_id, old2_id, voted):
    context = {}
    context["old1"] = get_object_or_404(Selfie, pk=old1_id)
    context["old2"] = get_object_or_404(Selfie, pk=old2_id)
    context["voted"] = voted

    n = len(Selfie.objects.all()) - 1
    context["s1"] = Selfie.objects.all()[randint(0, n)]
    context["s2"] = Selfie.objects.all()[randint(0, n)]
    return render(request, 'selfzone/index.html', context)


def upload(request):
    if request.method == 'POST':
        form = SelfieForm(request.POST, request.FILES)
        if form.is_valid():
            instance = Selfie(photo=request.FILES['photo'])
            instance.user = User.objects.all()[0]  # cecco
            instance.info = form.cleaned_data["info"]
            instance.save()
            return HttpResponse('Successful update')
        return HttpResponse('Data Not Valid')
    else:
        form = SelfieForm()
        return render(request, 'selfzone/uploadForm.html', {'form': form})


def vote(request, s1_id, s2_id, voted):
    s1 = get_object_or_404(Selfie, pk=s1_id)
    s2 = get_object_or_404(Selfie, pk=s2_id)

    if voted == "left":
        s1.won += 1
        s2.loss += 1
    elif voted == "right":
        s2.won += 1
        s1.loss += 1

    s1.save()
    s2.save()
    # return HttpResponse("Won " + str(sW.id) + ": " + str(sW.won) + "/" + str(sW.loss) + "\n" +
    #                    "Lost " + str(sL.id) + ": " + str(sL.won) + "/" + str(sL.loss) + "\n")
    return HttpResponseRedirect(reverse('selfzone:index_voted', args=(s1.id, s2.id, voted)))