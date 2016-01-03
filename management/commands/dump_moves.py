from collections import defaultdict
import json

from django.core.management.base import BaseCommand, CommandError
from ...models import *


class Command(BaseCommand):
    help = 'Pickles moves from positions ranked by quality.'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        with open("moves.dump", "w") as f:
            total = Position.objects.all().count()
            self.stdout.write("Total positions %d" % (total,))
            PAGE_LEN = 1000
            max_page = -(-total // PAGE_LEN)
            page = 0
            while True:
                qs = Position.objects.all()[page * PAGE_LEN:(page + 1) * PAGE_LEN]
                if not qs:
                    break
                self.stdout.write("Page %d / %d" % (page + 1, max_page))
                page += 1
                for position in qs:
                    if not position.position_infos.all().exists():
                        continue
                    code = position.states.all().first().code
                    board = code_to_board(code)
                    moves = {}
                    child_moves = {}
                    for coord, child in board.children(False):
                        child_code = board_to_code(child)
                        child_state = State.objects.filter(code=child_code).first()
                        if child_state:
                            child_position = child_state.position
                            transition, created = Transition.objects.get_or_create(source=position, target=child_position)
                            moves[coord] = transition.quality()
                            for child_coord, grand_child in child.children(False):
                                grand_child_code = board_to_code(grand_child)
                                grand_child_state = State.objects.filter(code=grand_child_code).first()
                                if grand_child_state:
                                    grand_child_position = grand_child_state.position
                                    transition, created = Transition.objects.get_or_create(source=child_position, target=grand_child_position)
                                    child_moves["%s-%s" % (coord, child_coord)] = transition.quality()
                    f.write("%s;%s;%s\n" % (code, json.dumps(moves), json.dumps(child_moves)))
