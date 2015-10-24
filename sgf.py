from hashlib import md5
import re

from go_board import Board
from models import *
from utils import *


add_black_re = re.compile(r'\WAB\[')
add_white_re = re.compile(r'\WAW\[')
black_player_re = re.compile(r'\WPB\[(.+?)\]')
white_player_re = re.compile(r'\WPW\[(.+?)\]')
black_rank_re = re.compile(r'\WBR\[(.+?)\]')
white_rank_re = re.compile(r'\WWR\[(.+?)\]')
result_re = re.compile(r'\WRE\[(.+?)\]')
size_re = re.compile(r'\WSZ\[(.+?)\]')
black_re = re.compile(r'\WB\[(..|)\]')
white_re = re.compile(r'\WW\[(..|)\]')


field_res = {
    "black_player": black_player_re,
    "black_rank": black_rank_re,
    "white_player": white_player_re,
    "white_rank": white_rank_re,
    "result": result_re,
    "date": re.compile(r'\WDT\[(.+?)\]'),
    "event": re.compile(r'\WEV\[(.+?)\]'),
    "round": re.compile(r'\WRO\[(.+?)\]'),
    "handicap": re.compile(r'\WHA\[(\d+?)\]'),
    "komi": re.compile(r'\WKM\[(.+?)\]'),
    "place": re.compile(r'\WPC\[(.+?)\]'),
    "rules": re.compile(r'\WRU\[(.+?)\]'),
    "time": re.compile(r'\WTM\[(\d+?)\]'),
    "overtime": re.compile(r'\WOT\[(.+?)\]'),
}


alpha = "abcdefghijklmnopqrstuvwxyz"


def process_sgf(sgf):
    black_player = black_player_re.search(sgf)
    black_player = black_player.group(1) if black_player else None
    white_player = white_player_re.search(sgf)
    white_player = white_player.group(1) if white_player else None
    if add_black_re.search(sgf):
        raise NotImplementedError("Add black")
    if add_white_re.search(sgf):
        raise NotImplementedError("Add white")
    size = int(size_re.search(sgf).group(1))
    if size != 9:
        raise ValueError("Only 9x9 supported")
    board = Board(size)
    black_moves = black_re.findall(sgf)
    white_moves = white_re.findall(sgf)
    player, opponent = black_moves, white_moves
    info = {}
    for name, field_re in field_res.items():
        field = field_re.search(sgf)
        field = field.group(1) if field else None
        info[name] = field
    info = parse_game_info(info)
    move_number = 0
    source = int_to_code(board.to_int(), GO_9x9_CODE_LENGTH)
    moves = []
    hasher = md5()
    while player:
        m = player.pop(0)
        if m:
            x = alpha.index(m[0])
            y = alpha.index(m[1])
            board.make_move(x, y)
        else:
            board.pass_()
        target = int_to_code(board.to_int(), GO_9x9_CODE_LENGTH)
        move_number += 1
        moves.append((source, target, move_number))
        hasher.update(target)

        player, opponent = opponent, player
        source = target

    info["hash"] = hasher.hexdigest()
    if GameInfo.objects.filter(**info).exists():
        return
        raise ValueError("Game already in DB")

    game_info = GameInfo.objects.create(**info)
    first = True
    for source_code, target_code, move_number in moves:
        if first:
            source, created = get_or_create_position(source_code)
            first = False
        else:
            source = target
        target, created = get_or_create_position(target_code)
        transition, created = Transition.objects.get_or_create(source=source, target=target)
        transition.times_played += 1
        transition.save()
        PositionInfo.objects.create(position=target, game_info=game_info, move_number=move_number)
