from random import randint

import os
from django.core.files import File
from django.core.management.base import BaseCommand, CommandError
from selfzone.models import *
from selfzone.management.utils import *
from selfzone.views import select_selfies


class Command(BaseCommand):
    help = 'Commands for data generation'
    possible_del = ["matches", "selfies", "tags", "users"]
    possible_gen = ["users", "selfies", "votes"]

    def add_arguments(self, parser):
        # Named (optional) arguments
        parser.add_argument(
            '--delete',
            action='store',
            default=False,
            nargs="*",
            help='Delete rows in tables',
        )
        parser.add_argument(
            '--gen',
            action='store',
            default=False,
            nargs="*",
            help='generate rows in tables',
        )
        parser.add_argument(
            '--autogen-votes',
            default=False,
            nargs="?", type=int,
            help='auto generate votes',
        )
        parser.add_argument(
            '--recalc',
            action='store_true',
            default=False,
            help='recalc scores and history',
        )

    def handle(self, *args, **options):
        if not(options["delete"] or options["gen"] or options["recalc"]) and options["autogen_votes"] is False:
            options["delete"] = []
            options["gen"] = []
            options["recalc"] = True

        if options["delete"] is not False:
            todel = options["delete"]
            if len(todel) == 0:
                todel = Command.possible_del

            if "matches" in todel and query_yn("delete matches?", "no"):
                History.objects.all().delete()
                Match.objects.all().delete()
            if "selfies" in todel and query_yn("delete selfies?", "no"):
                Selfie.objects.all().delete()
            if "tags" in todel and query_yn("delete tags?", "no"):
                Tag.objects.all().delete()
                Tag.init_tags()
            if "users" in todel and query_yn("delete users?", "no"):
                User.objects.all().delete()

        if options["gen"] is not False:
            togen = options["gen"]
            if len(togen) == 0:
                togen = Command.possible_gen

            if "users" in togen and query_yn("generate users?", "no"):
                gen_users()

            if "selfies" in togen and query_yn("generate selfies?", "no"):
                gen_selfies()

            if "votes" in togen and query_yn("generate votes?", "no"):
                gen_votes_wrapper()

        if options["recalc"] and query_yn("recalc all scores?", "no"):
            Selfie.recalculate_all()

        if options["autogen_votes"] is not False:
            num = 1000
            if options["autogen_votes"]:
                num = options["autogen_votes"]
            autogen_votes(num)


def gen_users():
    for i in range(0, 20):
        user = User.objects.create_user('cecco'+str(i), password='cecco')
        user.save()
        print user


def gen_selfies():
    real_stdout = sys.stdout
    fake_stdout = open(os.devnull, 'w')

    ass = open("ranking.ass", "w")
    selfies_imgs = {}
    path = None
    while True:
        try:
            path = raw_input("insert selfie import path:")
            rank = open(os.path.join(path, "ranking"), "r")
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
        user = User.objects.all()[randint(0, len(User.objects.all()) - 1)]
        s = Selfie()
        s.user = user
        s.photo = File(open(os.path.join(os.path.abspath(path), pic)))
        s.save()
        s.analyze()

        ass.write(str(s.id) + " " + str(selfies_imgs[pic]) + "\n")
        ass.flush()
        sys.stdout = real_stdout
        pbar.update(i)
    pbar.update(pbar.maxval)
    ass.close()
    print "analyze error selfies: ", Selfie.get_unrecognized().count()


def load_rankings():
    print "load rankings..."
    ranking = {}

    try:
        ass = open("ranking.ass", "r")
        for l in ass.readlines():
            l = l.split(" ")
            try:
                value = int(l[1])
                if value < 0 or value >= 10:
                    raise ValueError

                ranking[l[0]] = value
            except ValueError:
                print "error: rankings not valid at", l

        print "check rankings..."
        for s in Selfie.objects.all():
            if str(s.id) not in ranking:
                print s.id, "not found in ranking, ",
                if query_yn("assign standard rank?"):
                    ranking[str(s.id)] = 5
                else:
                    raise IOError
        print "rankig OK"
        return ranking

    except IOError:
        print "error: rankings not founds or corrupted!"


def autogen_votes(num):
    ranking = load_rankings()

    start_date = timezone.now() - timezone.timedelta(days=60)
    if Match.objects.count() >0:
        start_date = Match.objects.order_by("-match_date")[0].match_date
    end_date = timezone.now()
    delta = (end_date - start_date).total_seconds() / num
    print num, "matches to be generated"
    print "calc from", start_date, "to", end_date, "every", delta, "seconds,",
    if query_yn(" you want to proceed?"):
        gen_votes(ranking, start_date, delta, num)


def gen_votes_wrapper():
    ranking = load_rankings()
    while True:
        try:
            start_days = float(raw_input("start day: "))
            end_days = float(raw_input("end day: "))
            num = int(raw_input("num to calc: "))

            if start_days <0 or end_days <0 or num <0 or start_days < end_days:
                print "insert better values"
                continue

            start_date = timezone.now() - timezone.timedelta(days=start_days)
            end_date = timezone.now() - timezone.timedelta(days=end_days)
            delta = (end_date - start_date).total_seconds() / num
            print "calc from", start_date, "to", end_date, "every", delta, "seconds",
            if Match.objects.count()>0 and Match.objects.order_by("-match_date")[0].match_date > start_date:
                print "\nWARNING: there are matches after the start date, this can corrupt the score calculation,",
            if query_yn(" do you want to proceed?"):
                print "start generationg..."
                gen_votes(ranking, start_date, delta, num)
                break

        except ValueError:
            print "insert only integer values"
            continue


def gen_votes(ranking, start_date, delta, num):
    real_stdout = sys.stdout
    fake_stdout = open(os.devnull, 'w')

    tot = num
    pbar = ProgressBar(widgets=[' [', progressbar.Timer(), '] ', progressbar.Percentage(),
                                progressbar.Bar(), ' (', progressbar.ETA(), ') ']).start()
    pbar.maxval = tot

    with atomic():
        n = 0
        while n < num:
            sys.stdout = fake_stdout

            s1, s2 = select_selfies()
            s1_rank = ranking[str(s1.id)] * 1000
            s2_rank = ranking[str(s2.id)] * 1000
            if s1_rank > s2_rank:
                s1_rank *= 2
            else:
                s2_rank *= 2
            if randint(0, s1_rank + s2_rank) > s1_rank:
                Match.objects.create(winner=s2, loser=s1, match_date=start_date)
                s2.win_against(s1, start_date)
            else:
                Match.objects.create(winner=s1, loser=s2, match_date=start_date)
                s1.win_against(s2, start_date)

            sys.stdout = real_stdout
            start_date += timezone.timedelta(seconds=delta)
            n += 1
            if n > pbar.maxval:
                n = pbar.maxval
            pbar.update(n)
        pbar.update(pbar.maxval)
        print "\nsuccesfully generated", n, "matches, last gen: ", start_date
