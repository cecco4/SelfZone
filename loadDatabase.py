from selfzone.models import *
from django.contrib.auth.models import User
import os
from django.core.files import File
from django.contrib.auth.models import User
from random import randint
from selfzone.views import select_selfies
from django.db.transaction import atomic
import progressbar

import sys


def queryYN(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = raw_input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")

if queryYN("delete matches?", "no"):
    History.objects.all().delete()
    Match.objects.all().delete()
if queryYN("delete selfies?", "no"):
    Selfie.objects.all().delete()
if queryYN("delete tags?", "no"):
    Tag.objects.all().delete()
    Tag.init_tags()
if queryYN("delete users?", "no"):
    User.objects.all().delete()

if queryYN("create users?", "no"):
    for i in range(0, 20):
        user = User.objects.create_user('cecco'+str(i), password='cecco')
        user.save()
        print user

real_stdout = sys.stdout
fake_stdout = open(os.devnull, 'w')

if queryYN("reload selfies?", "no"):
    ass = open("ranking.ass","w")
    selfies_imgs = {}
    path = None
    while True:
        try:
            path = raw_input("insert selfie import path:")
            rank = open(os.path.join(path,"ranking"), "r")
            for img in rank.readlines()[1:]:
                vals = img.split(" ")
                selfies_imgs[vals[0]] = int(vals[1])
            break
        except IOError:
            print "path not valid"
            continue

    print str(len(selfies_imgs.keys())) + " selfies to upload..."
    pics = selfies_imgs.keys()
    pbar = ProgressBar(widgets=[' [', progressbar.Timer(), '] ', progressbar.Percentage(),
                                progressbar.Bar(), ' (', progressbar.ETA(), ') ']).start()
    tot = len(pics)
    pbar.maxval = tot

    for i in range(tot):
        sys.stdout = fake_stdout

        pic = pics[i]
        user = User.objects.all()[randint(0, len(User.objects.all())-1)]
        s = Selfie()
        s.user = user
        s.photo = File(open(os.path.join(os.path.abspath(path), pic)))
        s.save()
        s.analyze()

        ass.write(str(s.id)+" "+str(selfies_imgs[pic])+"\n")
        ass.flush()
        sys.stdout = real_stdout
        pbar.update(i)
    pbar.update(pbar.maxval)
    ass.close()
    print "analyze error selfies: ", Selfie.get_unrecognized().count()

if queryYN("generate votes"):
    print "load rankings..."
    ranking = {}
    try:
        ass = open("ranking.ass", "r")
        for l in ass.readlines():
            l = l.split(" ")
            ranking[l[0]] = int(l[1])

        while True:
            try:
                delta_days = int(raw_input("last days to calc:"))
                delta_sec = int(raw_input("delta time (secs):"))

                if delta_days <0 or delta_sec <0:
                    print "insert better values"
                    continue
                break
            except ValueError:
                print "insert only integer values"
                continue
        delta = timezone.timedelta(days=delta_days)
        start_date = timezone.now() - delta
        tot = delta.total_seconds()
        print "generating matches fro last ", delta_days, "days, every ", delta_sec, "secs"
        print "estimated matches to calc: ", tot/delta_sec
        pbar = ProgressBar(widgets=[' [', progressbar.Timer(), '] ', progressbar.Percentage(),
                                    progressbar.Bar(), ' (', progressbar.ETA(), ') ']).start()
        pbar.maxval = tot

        n=0
        while start_date < timezone.now():
            sys.stdout = fake_stdout

            s1, s2 = select_selfies()
            s1_rank = ranking[str(s1.id)]*1000
            s2_rank = ranking[str(s2.id)]*1000
            if s1_rank > s2_rank:
                s1_rank *= 2
            else:
                s2_rank *= 2
            if randint(0, s1_rank+s2_rank) > s1_rank:
                Match.objects.create(winner=s2, loser=s1, match_date=start_date)
            else:
                Match.objects.create(winner=s1, loser=s2, match_date=start_date)

            sys.stdout = real_stdout
            start_date += timezone.timedelta(seconds=delta_sec)
            n += delta_sec
            if n > pbar.maxval:
                n = pbar.maxval
            pbar.update(n)
        pbar.update(pbar.maxval)
        print ""

    except IOError:
        print "error: rankings not founds!"

if queryYN("recalculate all"):
    Selfie.recalculate_all()