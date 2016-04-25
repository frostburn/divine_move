from django.core.management.base import BaseCommand, CommandError
from ...models import *
from ...tsumego import query, TsumegoError


class Command(BaseCommand):
    help = 'Cache values on tsumego problems.'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        for problem in TsumegoProblem.objects.all():
            try:
                problem.value, _ = query(problem.state)
                problem.save()
            except TsumegoError:
                pass
