from django.core.management.base import BaseCommand, CommandError
from ...models import *
from ...go_board import *


class Command(BaseCommand):
    help = 'Does one step of negamax over the tree.'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        updated = 0
        total = Position.objects.all().count()
        for i, position in enumerate(Position.objects.all()):
            if i % 1000 == 0:
                self.stdout.write("%d / %d" % (i, total))
            old_low = position.low_score
            old_high = position.high_score
            # Constants chosen for debuging.
            new_low = -999
            new_high = -999
            qs = position.transitions.all().select_related('target')
            for transition in qs:
                child = transition.target
                if child.low_score is not None:
                    new_high = max(new_high, -child.low_score)
                if child.high_score is not None:
                    new_low = max(new_low, -child.high_score)
            if new_low == -999 or new_high == -999:
                if new_low != new_high:
                    raise Exception("Inconsistent scores.")
                continue
            if new_low != old_low or new_high != old_high:
                position.low_score = new_low
                position.high_score = new_high
                position.save()
                board = code_to_board(position.states.all().first().code)
                self.stdout.write(board.render())
                self.stdout.write("%s, %s -> %s, %s" % (old_low, old_high, new_low, new_high))
                updated += 1
        self.stdout.write("Done. %d positions updated." % updated)