from django.core.management.base import BaseCommand, CommandError
from ...models import *


class Command(BaseCommand):
    help = 'Pickles moves from positions ranked by quality.'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        with open("moves.dump", "w") as f:
            total = Position.objects.all().count()
            for i, position in enumerate(Position.objects.all()):
                if i % 1000 == 0:
                    self.stdout.write("%d / %d" % (i, total))
                qs = position.transitions.all()
                if qs.exists():
                    f.write(position.states.all().first().code + ":")
                    ms = []
                    for transition in qs:
                        ms.append("%s %s" % (transition.target.states.all().first().code, transition.quality()))
                    f.write(",".join(ms) + "\n")
