from django.core.management.base import BaseCommand, CommandError
from ...models import *
from ...go_board import *


class Command(BaseCommand):
    help = 'Repairs missing transitions between existing positions.'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        total = Position.objects.all().count()
        self.stdout.write("Total positions %d" % (total,))
        PAGE_LEN = 1000
        max_page = 1 + total // PAGE_LEN
        page = 0
        while True:
            qs = Position.objects.all()[page * PAGE_LEN:(page + 1) * PAGE_LEN]
            if not qs:
                break
            self.stdout.write("Page %d / %d" % (page + 1, max_page))
            page += 1
            for position in qs:
                board = code_to_board(position.states.all().first().code)
                for coord, child in board.children(False):
                    child_code = board_to_code(child)
                    child_state = State.objects.filter(code=child_code).first()
                    if child_state:
                        transition, created = Transition.objects.get_or_create(source=position, target=child_state.position)
                        if created:
                            self.stdout.write('Transition created between')
                            self.stdout.write(board.render())
                            self.stdout.write('and')
                            self.stdout.write(child.render())
