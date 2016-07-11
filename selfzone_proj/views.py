from django.shortcuts import render_to_response
from django.contrib.auth import logout
from django.http import HttpResponseRedirect

def main_page(request):
    return render_to_response('index.html')