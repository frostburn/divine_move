from django.core.management.base import BaseCommand, CommandError
from ...models import *


class Command(BaseCommand):
    help = 'Oneshot script to fix missing win statistics.'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        for game_info in GameInfo.objects.all():
            sign = game_info.result_sign()
            source = None
            for position_info in game_info.position_infos.all().order_by('move_number'):
                target = position_info.position
                if source is not None:
                    transition = Transition.objects.get(source=source, target=target)
                    if sign < 0:
                        transition.player_wins += 1
                    elif sign > 0:
                        transition.opponent_wins += 1
                    transition.save()
                source = target
                sign = -sign
