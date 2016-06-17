from django.shortcuts import render
from django.http import HttpResponse
from models import SelfieForm, Selfie
from django.contrib.auth.models import User
from random import randint


def index(request):
    n = len(Selfie.objects.all()) -1
    img1 = Selfie.objects.all()[randint(0, n)].photo
    img2 = Selfie.objects.all()[randint(0, n)].photo
    return render(request, 'selfzone/index.html', {'img1': img1, 'img2': img2})


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
