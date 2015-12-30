from hashlib import md5
import re

from go_board import Board
from models import *
from utils import *


add_black_re = re.compile(r'\WAB\[')
add_black_stones_re = re.compile(r'\WAB(\[..\])+')
add_white_re = re.compile(r'\WAW\[')
black_player_re = re.compile(r'\WPB\[(.*?)\]')
white_player_re = re.compile(r'\WPW\[(.*?)\]')
black_rank_re = re.compile(r'\WBR\[(.*?)\]')
white_rank_re = re.compile(r'\WWR\[(.*?)\]')
result_re = re.compile(r'\WRE\[(.*?)\]')
size_re = re.compile(r'\WSZ\[(.+?)\]')
black_re = re.compile(r'\WB\[(..|)\]')
white_re = re.compile(r'\WW\[(..|)\]')


field_res = {
    "black_player": black_player_re,
    "black_rank": black_rank_re,
    "white_player": white_player_re,
    "white_rank": white_rank_re,
    "result": result_re,
    "date": re.compile(r'\WDT\[(.*?)\]'),
    "game_name": re.compile(r'\WGN\[(.*?)\]'),
    "event": re.compile(r'\WEV\[(.*?)\]'),
    "round": re.compile(r'\WRO\[(.*?)\]'),
    "handicap": re.compile(r'\WHA\[(\d*?)\]'),
    "komi": re.compile(r'\WKM\[(.*?)\]'),
    "place": re.compile(r'\WPC\[(.*?)\]'),
    "rules": re.compile(r'\WRU\[(.*?)\]'),
    "time": re.compile(r'\WTM\[(\d*?)\]'),
    "overtime": re.compile(r'\WOT\[(.*?)\]'),
}


alpha = "abcdefghijklmnopqrstuvwxyz"


def process_sgf(sgf, serious=True):
    if add_white_re.search(sgf):
        raise NotImplementedError("Add white")
    size = int(size_re.search(sgf).group(1))
    if size != 13:
        raise ValueError("Only 13x13 supported")
    board = Board(size)
    flip = False
    if add_black_re.search(sgf):
        coords = add_black_stones_re.search(sgf).group(0).split("[")[1:]
        assert int(field_res["handicap"].search(sgf).group(1)) == len(coords)
        for coord in coords[:-1]:
            x = alpha.index(coord[0])
            y = alpha.index(coord[1])
            board.make_move(x, y)
            board.pass_()
        x = alpha.index(coords[-1][0])
        y = alpha.index(coords[-1][1])
        board.make_move(x, y)
        flip = True

    black_moves = black_re.findall(sgf)
    white_moves = white_re.findall(sgf)
    player, opponent = black_moves, white_moves
    if flip:
        player,opponent = opponent, player
    info = {}
    for name, field_re in field_res.items():
        field = field_re.search(sgf)
        field = field.group(1) if field else None
        info[name] = field
    info = parse_game_info(info)
    move_number = 0
    source = int_to_code(board.to_int(), CODE_LENGTH)
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
        target = int_to_code(board.to_int(), CODE_LENGTH)
        move_number += 1
        moves.append((source, target, move_number))
        hasher.update(target)

        player, opponent = opponent, player
        source = target
    if not moves:
        raise ValueError("Empty game")

    info["hash"] = hasher.hexdigest()
    info["is_serious"] = serious
    if GameInfo.objects.filter(**info).exists():
        return
        raise ValueError("Game already in DB")

    game_info = GameInfo.objects.create(**info)
    sign = game_info.result_sign()

    target_code, _, move_number = moves[0]
    target, created = get_or_create_position(target_code)
    if sign > 0:
        target.player_wins += 1
    elif sign < 0:
        target.opponent_wins += 1
    else:
        target.draws += 1
    target.save()
    PositionInfo.objects.create(position=target, game_info=game_info, move_number=0)

    for source_code, target_code, move_number in moves:
        sign = -sign
        source = target
        target, created = get_or_create_position(target_code)
        transition, created = Transition.objects.get_or_create(source=source, target=target)
        if serious:
            transition.times_played += 1
            if sign > 0:
                target.player_wins += 1
            elif sign < 0:
                target.opponent_wins += 1
            else:
                target.draws += 1
            target.save()
            transition.save()
        PositionInfo.objects.create(position=target, game_info=game_info, move_number=move_number)


def remove_game(game_info):
    sign = game_info.result_sign()
    source = None
    for position_info in game_info.position_infos.all().order_by('move_number'):
        target = position_info.position
        if game_info.is_serious:
            if sign > 0:
                target.player_wins -= 1
            elif sign < 0:
                target.opponent_wins -= 1
            else:
                target.draws -= 1
            target.save()
        if source is not None and game_info.is_serious:
            transition = Transition.objects.get(source=source, target=target)
            transition.times_played -= 1
            transition.save()
        position_info.delete()
        source = target
        sign = -sign
    game_info.delete()
