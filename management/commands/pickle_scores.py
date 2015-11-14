import cPickle as pickle

from django.core.management.base import BaseCommand, CommandError
from ...models import *


class Command(BaseCommand):
    help = 'Pickles the scores of positions.'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        scores = {}
        for position in Position.objects.all():
            if position.low_score is not None:
                scores[position.states.all().first().code] = position.low_score
        with open("scores.pickle", "w") as f:
            pickle.dump(scores, f)
        self.stdout.write("Done. %d positions with score pickled." % len(scores))
