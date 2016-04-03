# -*- coding: utf-8 -*-
import os
from math import log, ceil
import random

from django.conf import settings
import pexpect

from go_board import ALPHA, popcount
from utils import *


WIDTH = 9
HEIGHT = 7
STATE_SIZE = WIDTH * HEIGHT
H_SHIFT = 1
V_SHIFT = WIDTH
D_SHIFT = WIDTH - 1
NORTH_WALL = (1 << WIDTH) - 1
WEST_WALL = 0x40201008040201
WEST_BLOCK = 0X3FDFEFF7FBFDFEFF

TARGET_SCORE = 63


def rectangle(width, height):
    r = 0
    for i in range(width):
        for j in range(height):
            r |= 1 << (i * H_SHIFT + j * V_SHIFT)
    return r


def flood(source, target):
    source &= target
    # Disabled until further testing.
    # temp = WEST_BLOCK & target
    # source |= temp & ~((source & WEST_BLOCK) + temp)
    while True:
        temp = source
        source |= (
            ((source & WEST_BLOCK) << H_SHIFT) |
            ((source >> H_SHIFT) & WEST_BLOCK) |
            (source << V_SHIFT) |
            (source >> V_SHIFT)
        ) & target
        if temp == source:
            break
    return source


def chains(stones):
    result = []
    for i in range(STATE_SIZE):
        m = 1 << i
        if m & stones:
            chain = flood(m, stones)
            result.append(chain)
            stones ^= chain
    return result


def north(stones):
    return stones >> V_SHIFT


def south(stones):
    return stones << V_SHIFT


def west(stones):
    return (stones >> H_SHIFT) & WEST_BLOCK


def east(stones):
    return (stones & WEST_BLOCK) << H_SHIFT


def liberties(stones, empty):
    return (
        ((stones & WEST_BLOCK) << H_SHIFT) |
        ((stones >> H_SHIFT) & WEST_BLOCK) |
        (stones << V_SHIFT) |
        (stones >> V_SHIFT)
    ) & ~stones & empty


def to_coord_list(stones):
    result = []
    for x in range(WIDTH):
        for y in range(HEIGHT):
            if stones & (1 << (x * H_SHIFT + y * V_SHIFT)):
                result.append([x, y])
    return result


def to_coords(move):
    if not move:
        return []
    if popcount(move) != 1:
        raise ValueError("Not a single stone move")
    return to_coord_list(move)[0]


def render_stones(stones):
    r = u""
    for y in xrange(HEIGHT):
        r += str(y)
        for x in xrange(WIDTH):
            m = 1 << (x + y * V_SHIFT)
            r += u"\x1b[0;30;43m"  # Yellow bg
            if stones & m:
                r += u"\x1b[30m ●"
            else:
                r += u"\x1b[30m ·";
        r += u"\x1b[0m\n"
    r += u" "
    for x in xrange(WIDTH):
        r += u" " + ALPHA[x]
    return r


class TsumegoError(Exception):
    pass


class State(object):
    num_code_chars = 63

    def __init__(
            self,
            playing_area,
            player=0,
            opponent=0,
            ko=0,
            target=0,
            immortal=0,
            passes=0,
            ko_threats=0,
            white_to_play=False,
            captures_by_player=0,
            captures_by_opponent=0,
            min_ko_threats=float("-inf"),
            max_ko_threats=float("inf"),
        ):
        self.playing_area = playing_area
        self.player = player
        self.opponent = opponent
        self.ko = ko
        self.target = target
        self.immortal = immortal
        self.passes = passes
        self.ko_threats = ko_threats
        self.white_to_play = white_to_play

        self.captures_by_player = captures_by_player
        self.captures_by_opponent = captures_by_opponent

        self.min_ko_threats = min_ko_threats
        self.max_ko_threats = max_ko_threats

        open_area = playing_area & ~(target | immortal)
        self.moves = [0]
        for i in range(STATE_SIZE):
            move = 1 << i
            if move & open_area:
                self.moves.append(move)

        self.last_move = -1

        row_widths = []
        for j in reversed(range(HEIGHT)):
            width = 0
            for i in reversed(range(WIDTH)):
                if self.playing_area & (1 << (i + j * V_SHIFT)):
                    width = i + 1
                    break
            if width or row_widths:
                row_widths.append(width)
        self.row_widths = row_widths[::-1]
        self.width = max(row_widths)
        self.height = len(row_widths)

    def copy(self):
        return State(
            self.playing_area,
            self.player,
            self.opponent,
            self.ko,
            self.target,
            self.immortal,
            self.passes,
            self.ko_threats,
            self.white_to_play,
            self.captures_by_player,
            self.captures_by_opponent,
            self.min_ko_threats,
            self.max_ko_threats,
        )

    def empty(self):
        fixed = self.target | self.immortal
        self.player &= fixed
        self.opponent &= fixed
        self.ko = 0
        self.passes = 0
        self.ko_threats = 0
        self.captures_by_player = 0
        self.captures_by_opponent = 0

    def set_layers(self, num_layers):
        if abs(self.ko_threats) >= num_layers:
            raise ValueError("Not enough layers to reach zero ko threats")
        if self.ko_threats > 0:
            self.min_ko_threats = self.ko_threats - num_layers + 1
            self.max_ko_threats = self.ko_threats
        elif self.ko_threats < 0:
            self.min_ko_threats = self.ko_threats
            self.max_ko_threats = self.ko_threats + num_layers - 1
        else:
            self.min_ko_threats = 0
            self.max_ko_threats = 0

    def _kill_chain(self, chain):
        empty = self.playing_area & ~self.player
        if not liberties(chain, empty) and not (chain & self.immortal):
            self.opponent ^= chain
            if not (chain & self.target):
                return chain
        return 0

    def swap_players(self):
        self.player, self.opponent = (self.opponent, self.player)
        self.ko_threats = -self.ko_threats
        self.white_to_play = not self.white_to_play
        self.captures_by_player, self.captures_by_opponent = (self.captures_by_opponent, self.captures_by_player)
        self.min_ko_threats, self.max_ko_threats = -self.max_ko_threats, -self.min_ko_threats

    def make_move(self, move):
        if not self.active:
            return False, 0
        if not move:
            if self.ko:
                self.ko = 0
            else:
                self.passes += 1
            self.swap_players()
            self.last_move = move
            return True, 0

        old_player = self.player
        old_opponent = self.opponent
        old_ko = self.ko
        old_ko_threats = self.ko_threats
        if move & self.ko:
            if self.ko_threats <= 0:
                return False, 0
            self.ko_threats -= 1

        if move & (self.player | self.opponent | ~self.playing_area):
            return False, 0

        self.player |= move
        kill = 0
        empty = self.playing_area & ~self.player
        chain = flood(north(move), self.opponent)
        kill |= self._kill_chain(chain)
        chain = flood(south(move), self.opponent)
        kill |= self._kill_chain(chain)
        chain = flood(west(move), self.opponent)
        kill |= self._kill_chain(chain)
        chain = flood(east(move), self.opponent)
        kill |= self._kill_chain(chain)

        self.ko = 0
        num_kill = popcount(kill)
        if (num_kill == 1):
            if liberties(move, self.playing_area & ~self.opponent) == kill:
                self.ko = kill
        chain = flood(move, self.player)
        if not liberties(chain, self.playing_area & ~self.opponent) and not (chain & self.immortal):
            self.player = old_player
            self.opponent = old_opponent
            self.ko = old_ko
            self.ko_threats = old_ko_threats
            return False, 0

        self.captures_by_player += num_kill

        self.passes = 0
        self.swap_players()
        self.last_move = move

        return True, num_kill

    def add_player(self, move):
        result = self.make_move(move)
        self.swap_players()
        self.last_move = -1
        return result

    def add_opponent(self, move):
        self.swap_players()
        self.last_move = -1
        return self.make_move(move)

    def remove(self, move):
        self.player &= ~move
        self.opponent &= ~move
        self.last_move = -1

    @property
    def target_dead(self):
        return bool(self.target & ~(self.player | self.opponent))

    @property
    def active(self):
        return self.passes < 2 and not self.target_dead

    def fix_targets(self):
        """
        Kill targets without liberties.
        """
        player_dead = False
        opponent_dead = False
        for chain in chains(self.player & self.target):
            if not liberties(chain, self.playing_area & ~self.opponent) and not (chain & self.immortal):
                self.player ^= chain
                player_dead = True
        for chain in chains(self.opponent & self.target):
            if not liberties(chain, self.playing_area & ~self.player) and not (chain & self.immortal):
                self.opponent ^= chain
                opponent_dead = True
        return player_dead, opponent_dead

    def render(self):
        if self.white_to_play:
            black = self.opponent
            white = self.player
        else:
            black = self.player
            white = self.opponent
        r = u""
        for y in xrange(HEIGHT):
            r += str(y)
            for x in xrange(WIDTH):
                m = 1 << (x + y * V_SHIFT)
                if m & self.target:
                    r += u"\x1b[0;30;41m"  # Red bg
                elif m & self.immortal:
                    r += u"\x1b[0;30;42m"  # Green bg
                elif m & self.playing_area:
                    r += u"\x1b[0;30;43m"  # Yellow bg
                else:
                    r += u"\x1b[0m"
                if black & m:
                    r += u"\x1b[30m ●"
                elif white & m:
                    r += u"\x1b[37m ●"
                elif self.ko & m:
                    r += u"\x1b[30m □"
                elif m & self.playing_area:
                    r += u"\x1b[30m ·";
            r += u"\x1b[0m\n"
        r += u" "
        for x in xrange(WIDTH):
            r += u" " + ALPHA[x]
        r += u"\n"
        if self.white_to_play:
            r += u"White to play"
        else:
            r += u"Black to play"
        r += u", passes=%d, ko_threats=%d, prisoners=%d, %d" % (self.passes, self.ko_threats, self.captures_by_player, self.captures_by_opponent)
        return r

    def dump(self):
        return "%d %d %d %d %d %d %d %d %d" % (
            self.playing_area,
            self.player,
            self.opponent,
            self.ko,
            self.target,
            self.immortal,
            self.passes,
            self.ko_threats,
            self.white_to_play
        )

    def get_colors(self):
        if self.white_to_play:
            white = self.player
            black = self.opponent
        else:
            black = self.player
            white = self.opponent
        return black, white

    def get_prisoners(self):
        if self.white_to_play:
            return self.captures_by_opponent, self.captures_by_player
        else:
            return self.captures_by_player, self.captures_by_opponent

    @property
    def code_size(self):
        max_code = 3 ** len(self.moves) * (3 + len(self.moves)) * 2
        return int(ceil(log(max_code, self.num_code_chars)))

    def to_code(self):
        black, white = self.get_colors()
        code = 0
        ko_pos = 0
        for i, m in enumerate(sorted(self.moves)):
            code *= 3
            if black & m:
                code += 1
            elif white & m:
                code += 2
            if self.ko & m:
                ko_pos = i
            i += 1
        if not self.ko:
            ko_pos = len(self.moves)
        if self.passes:
            assert not self.ko
            assert self.passes <= 2
            ko_pos += self.passes
        code *= 3 + len(self.moves)
        code += ko_pos
        code *= 2
        code += 1 if self.white_to_play else 0

        code = int_to_code(code, self.code_size, num_chars=self.num_code_chars)
        if self.ko_threats:
            code += "_%d" % (self.ko_threats,)
        if self.captures_by_player or self.captures_by_opponent:
            code += "_%d_%d" % (self.captures_by_player, self.captures_by_opponent)

        return code

    def from_code(self, code):
        other = self.copy()
        fixed = self.target | self.immortal
        other.player &= fixed
        other.opponent &= fixed

        other.ko_threats, other.captures_by_player, other.captures_by_opponent = (0, 0, 0)
        if "_" in code:
            code, rest = code.split("_", 1)
            if rest.count("_") == 0:
                other.ko_threats = int(rest)
            elif rest.count("_") == 1:
                other.captures_by_player, other.captures_by_opponent = map(int, rest.split("_"))
            elif rest.count("_") == 2:
                other.ko_threats, other.captures_by_player, other.captures_by_opponent = map(int, rest.split("_"))
            else:
                raise TsumegoError("Invalid code")

        code = code_to_int(code, num_chars=self.num_code_chars)
        other.white_to_play = bool(code % 2)
        code //= 2
        ko_pos = code % (3 + len(self.moves))
        code //= (3 + len(self.moves))
        if ko_pos < len(self.moves):
            other.ko = sorted(self.moves)[ko_pos]
        else:
            other.passes = ko_pos - len(self.moves)
        black = 0
        white = 0
        for m in reversed(sorted(self.moves)):
            stone = code % 3
            code //= 3
            if stone == 1:
                black |= m
            elif stone == 2:
                white |= m
        if other.white_to_play != self.white_to_play:
            other.player, other.opponent = other.opponent, other.player
            other.min_ko_threats, other.max_ko_threats = -other.max_ko_threats, -other.min_ko_threats
        if other.white_to_play:
            other.player |= white
            other.opponent |= black
        else:
            other.player |= black
            other.opponent |= white
        return other

    # TODO: Make use of in react compatible way
    def _get_json_members(self, color, name):
        color_target = flood(self.target, color)
        color_immortal = flood(self.immortal, color)
        color_escaped = color_target & color_immortal
        color ^= color_target | color_immortal
        color_target ^= color_escaped
        color_immortal ^= color_escaped

        result = {}
        result[name] = color
        result[name + "_target"] = color_target
        result[name + "_immortal"] = color_immortal
        result[name + "_escaped"] = color_escaped

        for key, value in result.items():
            result[key] = to_coord_list(value)

        return result

    def to_json(self):
        black, white = self.get_colors()
        captures_by_black, captures_by_white = self.get_prisoners()

        moves = 0
        o_moves = 0
        for move in self.moves:
            child = self.copy()
            valid, prisoners = child.make_move(move)
            if valid:
                moves |= move
            child = self.copy()
            child.swap_players()
            valid, prisoners = child.make_move(move)
            if valid:
                o_moves |= move

        color_to_play = ("white" if self.white_to_play else "black")
        o_color = ("black" if self.white_to_play else "white")
        rows = []
        for j in range(len(self.row_widths)):
            row = []
            for i in range(self.row_widths[j]):
                # Most of the JSON response is stone data so we compress it to single letters in the interest of bandwidth.
                m = 1 << (i + j * V_SHIFT)
                if m & black:
                    color = "b"
                elif m & white:
                    color = "w"
                elif m & self.ko:
                    color = "k"
                else:
                    color = "n"

                pa = self.playing_area
                horizontal = ""
                vertical = ""
                if m & pa:
                    if m & east(pa):
                        horizontal += "e"
                    if m & west(pa):
                        horizontal += "w"
                    if m & north(pa):
                        vertical += "n"
                    if m & south(pa):
                        vertical += "s"

                stone = {
                    "c": color,
                    "x": "%d_%d" % (i, j),
                }
                if vertical:
                    stone["v"] = vertical
                    if not horizontal:
                        stone["h"] = "d"
                if horizontal:
                    stone["h"] = horizontal
                    if not vertical:
                        stone["v"] = "d"
                if m & moves:
                    stone["m"] = True
                if m & o_moves:
                    stone["o"] = True
                if (self.last_move > 0) and (m & self.last_move):
                    stone["l"] = True
                row.append(stone)
            rows.append({
                "index": j,
                "stones": row,
            })

        status = ""
        if not self.last_move and not self.passes:
            status = "The opponent passed clearing a ko."
        if self.passes == 1:
            status = "The opponent passed."
        elif self.passes >= 2:
            status = "The game has ended."
        if self.target_dead:
            status = "Target eliminated."

        result = {
            "code": self.to_code(),
            "passes": self.passes,
            "ko_threats": self.ko_threats,
            "white_to_play": self.white_to_play,
            "captures_by_black": captures_by_black,
            "captures_by_white": captures_by_white,
            "min_ko_threats": self.min_ko_threats,
            "max_ko_threats": self.max_ko_threats,
            "active": self.active,
            "status": status,
            "rows": rows,
            "width": self.width,
            "height": self.height,
            "dump": self.dump(),
        }

        return result

    @classmethod
    def load(cls, dump):
        instance = cls(*map(int, dump.split(" ")))
        instance.white_to_play = bool(instance.white_to_play)
        return instance

    def update(self, dump):
        other = State.load(dump)
        self.player = other.player
        self.opponent = other.opponent
        self.ko = other.ko


class NodeValue(object):
    def __init__(self, low, high, low_distance, high_distance):
        self.low = low
        self.high = high
        self.low_distance = low_distance
        self.high_distance = high_distance

    @property
    def valid(self):
        return (self.low <= self.high and self.low_distance >= 0 and self.high_distance >= 0)

    @property
    def error(self):
        if self.low > self.high:
            if self.low_distance and self.high_distance:
                return "Tsumego not in DB"
            if not self.low_distance:
                return "Invalid layer"
            if not self.high_distance:
                return "Invalid key"
        return ""

    def low_child(self, other, prisoners=0):
        return -other.high + prisoners == self.low and other.high_distance + 1 == self.low_distance

    def high_child(self, other, prisoners=0):
        return -other.low + prisoners == self.high and other.low_distance + 1 == self.high_distance

    def add_prisoners(self, prisoners):
        self.low -= prisoners
        self.high -= prisoners

    def __repr__(self):
        return "%s(%d, %d, %d, %d)" % (self.__class__.__name__, self.low, self.high, self.low_distance, self.high_distance)

    def to_json(self):
        return {
            "low": self.low,
            "high": self.high,
            "low_distance": self.low_distance,
            "high_distance": self.high_distance,
        }


_QUERY = None
BASE_STATES = {"design": State(rectangle(9, 7))}
BASE_STATES["design"].set_layers(1)


def reset_query():
    global _QUERY
    _QUERY = None
    return "DB reset"


def init_query():
    global _QUERY, BASE_STATES
    if _QUERY is None:
        os.chdir(settings.TSUMEGO_QUERY_PATH)
        filenames = [name + "_japanese.dat" for name in settings.TSUMEGO_NAMES]
        _QUERY = pexpect.spawn("./query " + " ".join(filenames), echo=False)
        for name in settings.TSUMEGO_NAMES:
            _QUERY.expect(" ".join(["-?\d+"] * 9))
            BASE_STATES[name] = State.load(_QUERY.after)
            _QUERY.expect("\d")
            BASE_STATES[name].set_layers(int(_QUERY.after))
            if settings.LOCAL_DEBUG:
                print BASE_STATES[name].render()
        _QUERY.expect("Solutions loaded.")
        if settings.LOCAL_DEBUG:
            print "Solutions loaded"
    return BASE_STATES


def query(state, reverse_target=False):
    os.chdir(settings.TSUMEGO_QUERY_PATH)
    if _QUERY is None:
        raise ValueError("Call init_query first")
    player_dead, opponent_dead = state.fix_targets()
    if player_dead and opponent_dead:
        raise ValueError("Inconsistent target kill")
    if player_dead:
        return NodeValue(-TARGET_SCORE, -TARGET_SCORE, 0, 0), {}
    elif opponent_dead:
        return NodeValue(TARGET_SCORE, TARGET_SCORE, 0, 0), {}
    if state.target_dead:
        if reverse_target:
            return NodeValue(TARGET_SCORE, TARGET_SCORE, 0, 0), {}
        else:
            return NodeValue(-TARGET_SCORE, -TARGET_SCORE, 0, 0), {}
    _QUERY.sendline(state.dump())
    _QUERY.expect("-?\d+ -?\d+ \d+ \d+")
    out = map(int, _QUERY.after.split(" "))
    v = NodeValue(*out)
    _QUERY.expect("\d+")
    num_children = int(_QUERY.after)
    children = {}
    for i in range(num_children):
        _QUERY.expect("\d+ -?\d+ -?\d+ \d+ \d+")
        out = map(int, _QUERY.after.split(" "))
        children[out[0]] = NodeValue(*out[1:])
    return v, children


def get_coords():
    while True:
        coords = raw_input("Enter coordinates: ").upper()
        if coords.startswith("PASS"):
            return None
        else:
            try:
                if coords[0].isalpha():
                    x = ALPHA.index(coords[0])
                    y = int(coords[1])
                else:
                    x = ALPHA.index(coords[1])
                    y = int(coords[0])
            except ValueError, IndexError:
                print "Invalid coordinates!"
                continue
        return x, y


def format_value(state, value):
    result = -value.low if state.white_to_play else value.low
    captures_by_black, captures_by_white = state.get_prisoners()
    result += captures_by_black - captures_by_white
    if result < 0:
        result = "W+" + str(-result)
    else:
        result = "B+" + str(result)
    return result


def get_result(state):
    value, children = query(state)
    if not value.valid:
        raise TsumegoError(value.error)
    return format_value(state, value)


def get_full_result(state):
    value, children = query(state)
    r = format_value(state, value) + "\n"
    for move in state.moves:
        if move not in children:
            continue
        child = state.copy()
        valid, prisoners = child.make_move(move)
        if valid:
            child_value = children[move]
            r += format_value(child, child_value) + " "
    return r


def make_book_move(state, low=False):
    value, children = query(state)
    if not value.valid:
        raise TsumegoError(value.error)
    random.shuffle(state.moves)
    for move in state.moves:
        if move not in children:
            continue
        child = state.copy()
        valid, prisoners = child.make_move(move)
        if valid:
            child_value = children[move]
            high_child = value.high_child(child_value, prisoners)
            low_child = value.low_child(child_value, prisoners)
            if (low_child if low else high_child):
                state.make_move(move)
                return child_value


def demo(tsumego_name="4x4", ko_threats=0):
    init_query()
    state = BASE_STATES[tsumego_name].copy()
    state.ko_threats = ko_threats
    print state.render()
    while state.active:
        assert(not state.white_to_play)
        while True:
            coords = get_coords()
            if coords is None:
                state.make_move(0)
                break
            else:
                valid, prisoners = state.make_move(1 << (coords[0] * H_SHIFT + coords[1] * V_SHIFT))
                if valid:
                    break
                else:
                    print "Invalid move!"
        print state.render()
        if not state.active:
            break

        value, children = query(state)
        random.shuffle(state.moves)
        for move in state.moves:
            if move not in children:
                continue
            child = state.copy()
            valid, prisoners = child.make_move(move)
            if valid:
                child_value = children[move]
                if value.high_child(child_value, prisoners):
                    state = child
                    value = child_value
                    break
        else:
            raise IndexError("Inconsistent query database.")
        print state.render()

    result = get_result(state)
    print "Result %s" % result

def design(width, height):
    # state = State(rectangle(width, height))
    state = State.load("8744452554367 8735980290112 4164952080 0 4164952080 8735980290112 0 0 0")
    # state = State.load("8744452554367 8740283662432 4168891416 0 4164952080 8735980290112 0 0 0")  # Bent four in the corner
    state = State.load("8744452554367 4168884754 8740283665508 0 4164952080 8735980290112 0 0 1")  # Ten thousand year ko
    state.swap_players()
    state.ko_threats = 1
    while True:
        print state.render()
        print get_full_result(state)
        print state.dump()
        if not state.active:
            break
        while True:
            coords = get_coords()
            if coords is None:
                state.make_move(0)
                break
            else:
                valid, prisoners = state.make_move(1 << (coords[0] * H_SHIFT + coords[1] * V_SHIFT))
                if valid:
                    break
                else:
                    print "Invalid move!"
