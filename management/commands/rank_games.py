from __future__ import division
import cPickle as pickle

from django.core.management.base import BaseCommand, CommandError
from ...models import *
from ...models import _rank_to_q


def rank_to_elo(rank):
    if rank is None:
        return None
    rank = rank.lower()
    rank = rank.replace(" ", "")
    rank = rank.replace("pro", "p")
    rank = rank.replace("dan", "d")
    rank = rank.replace("kyu", "k")
    try:
        if rank.endswith("k"):
            return 1800 - int(rank[:-1]) * 100
        elif rank.endswith("d"):
            return 1700 + int(rank[:-1]) * 100
        elif rank.endswith("p"):
            return 1800 + int(rank[:-1]) * 100
    except ValueError:
        return None
    return None


def elo_to_rank(elo):
    elo //= 100
    if elo < 18:
        return "%dk" % (18 - elo)
    return "%dd" % (elo - 17)


class Command(BaseCommand):
    help = 'Something something ranking.'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        players = {}
        ranks = {}
        for game_info in GameInfo.objects.all():
            for p, r in [(game_info.black_player, game_info.black_rank), (game_info.white_player, game_info.white_rank)]:
                e = rank_to_elo(r)
                if e is not None:
                    if p in players:
                        if e > players[p]:
                            players[p] = e
                            ranks[p] = r
                    else:
                        players[p] = e
                        ranks[p] = r
        for game_info in GameInfo.objects.all():
            for p in [game_info.black_player, game_info.white_player]:
                if p not in players:
                    players[p] = 1500
        for game_info in GameInfo.objects.all():
            b = game_info.black_player
            w = game_info.white_player
            r1 = 10 ** (players[b] / 400)
            r2 = 10 ** (players[w] / 400)
            e1 = r1 / (r1 + r2)
            e2 = r2 / (r1 + r2)
            s = game_info.result_sign()
            if s > 0:
                s1 = 1
                s2 = 0
            elif s < 0:
                s1 = 0
                s2 = 1
            else:
                s1 = 0.5
                s2 = 0.5
            K = 32
            players[b] += K * (s1 - e1)
            players[w] += K * (s2 - e1)
        for e, p in sorted([(e, p) for p, e in players.items()], reverse=True):
            if p not in ranks:
                self.stdout.write("%s: %s %s" % (p, e, elo_to_rank(e)))
                u = raw_input()
                if u == 'y':
                    u = elo_to_rank(e)
                elif u == 'n':
                    continue
                ranks[p] = u
        for game_info in GameInfo.objects.all():
            if not game_info.black_rank:
                if game_info.black_player in ranks:
                    game_info.black_rank = ranks[game_info.black_player]
            if not game_info.white_rank:
                if game_info.white_player in ranks:
                    game_info.white_rank = ranks[game_info.white_player]
            game_info.quality = _rank_to_q(game_info.black_rank) + _rank_to_q(game_info.white_rank)
            game_info.save()
