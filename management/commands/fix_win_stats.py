from django.core.management.base import BaseCommand, CommandError
from ...models import *


class Command(BaseCommand):
    help = 'Oneshot script to fix missing win statistics.'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        for game_info in GameInfo.objects.all():
            if not game_info.is_serious:
                continue
            sign = game_info.result_sign()
            for position_info in game_info.position_infos.all().order_by('move_number'):
                position = position_info.position
                if sign > 0:
                    position.player_wins += 1
                elif sign < 0:
                    position.opponent_wins += 1
                else:
                    position.draws += 1
                position.save()
                sign = -sign
