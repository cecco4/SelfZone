from django.shortcuts import render_to_response
from django.contrib.auth import logout
from django.http import HttpResponseRedirect


def logout_view(request):
    "Log users out and re-direct them to the main page."
    logout(request)
    return HttpResponseRedirect('/')


def main_page(request):
    return render_to_response('index.html')