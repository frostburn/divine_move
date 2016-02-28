# -*- coding: utf-8 -*-
from django.conf import settings

from go_board import ALPHA, popcount


WIDTH = 9
HEIGHT = 7
STATE_SIZE = WIDTH * HEIGHT
H_SHIFT = 1
V_SHIFT = WIDTH
D_SHIFT = WIDTH - 1
NORTH_WALL = (1 << WIDTH) - 1
WEST_WALL = 0x40201008040201
WEST_BLOCK = 0X3FDFEFF7FBFDFEFF


def rectangle(width, height):
    r = 0
    for i in range(width):
        for j in range(height):
            r |= 1 << (i * H_SHIFT + j * V_SHIFT)
    return r


def flood(source, target):
    source &= target
    temp = WEST_BLOCK & target
    source |= temp & ~(source + temp)
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


class State(object):
    def __init__(self, playing_area, player=0, opponent=0, ko=0, target=0, immortal=0, passes=0, ko_threats=0, white_to_play=False):
        self.playing_area = playing_area
        self.player = player
        self.opponent = opponent
        self.ko = ko
        self.target = target
        self.immortal = immortal
        self.passes = passes
        self.ko_threats = ko_threats
        self.white_to_play = white_to_play

        self.black_prisoners = 0
        self.white_prisoners = 0

        open_area = playing_area & ~(target | immortal)
        self.moves = [0]
        for i in range(STATE_SIZE):
            move = 1 << i
            if move & open_area:
                self.moves.append(move)

    def copy(self):
        c = State(
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
        c.black_prisoners = self.black_prisoners
        c.white_prisoners = self.white_prisoners
        c.moves = self.moves[:]
        return c

    def make_move(self, move):
        old_player = self.player
        if not move:
            if self.ko:
                self.ko = 0
            else:
                self.passes += 1
            self.player = self.opponent
            self.opponent = old_player
            self.ko_threats = -self.ko_threats
            self.white_to_play = not self.white_to_play
            return True, 0
        
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
        if not liberties(chain, empty) and not (chain & self.immortal):
            kill |= chain
            self.opponent ^= chain
        chain = flood(south(move), self.opponent)
        if not liberties(chain, empty) and not (chain & self.immortal):
            kill |= chain
            self.opponent ^= chain
        chain = flood(west(move), self.opponent)
        if not liberties(chain, empty) and not (chain & self.immortal):
            kill |= chain
            self.opponent ^= chain
        chain = flood(east(move), self.opponent)
        if not liberties(chain, empty) and not (chain & self.immortal):
            kill |= chain
            self.opponent ^= chain

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

        if self.white_to_play:
            self.black_prisoners += num_kill
        else:
            self.white_prisoners += num_kill

        self.passes = 0
        old_player = self.player
        self.player = self.opponent
        self.opponent = old_player
        self.ko_threats = -self.ko_threats
        self.white_to_play = not self.white_to_play
        return True, num_kill

    def target_dead(self):
        return bool(self.target & ~(self.player | self.opponent))

    def active(self):
        return self.passes < 2 and not self.target_dead()

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
        r += u", passes=%d, ko_threats=%d, prisoners=%d, %d" % (self.passes, self.ko_threats, self.black_prisoners, self.white_prisoners)
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


class NodeValue(object):
    def __init__(self, low, high, low_distance, high_distance):
        self.low = low
        self.high = high
        self.low_distance = low_distance
        self.high_distance = high_distance

    def low_child(self, other, prisoners=0):
        return -other.high + prisoners == self.low and other.high_distance + 1 == self.low_distance

    def high_child(self, other, prisoners=0):
        return -other.low + prisoners == self.high and other.low_distance + 1 == self.high_distance

    def __repr__(self):
        return "%s(%d, %d, %d, %d)" % (self.__class__.__name__, self.low, self.high, self.low_distance, self.high_distance)


_QUERY = None


def query(state):
    import os
    import pexpect
    global _QUERY
    os.chdir(settings.TSUMEGO_QUERY_PATH)
    if _QUERY is None:
        _QUERY = pexpect.spawn("./query", echo=False)
        _QUERY.expect("Solutions loaded.")
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


def demo():
    import random
    state = State(rectangle(4, 4))
    print state.render()
    while state.active():
        assert(not state.white_to_play)
        while True:
            coords = raw_input("Enter coordinates: ").upper()
            if coords.startswith("PASS"):
                state.make_move(0)
                break
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
                valid, prisoners = state.make_move(1 << (x * H_SHIFT + y * V_SHIFT))
                if valid:
                    break
                else:
                    print "Invalid coordinates!"
        print state.render()
        if not state.active():
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

    value, children = query(state)
    if state.white_to_play:
        result = -value.high + state.black_prisoners - state.white_prisoners
    else:
        result = value.low + state.white_prisoners - state.black_prisoners
    if result < 0:
        result = "W+" + str(-result)
    else:
        result = "B+" + str(result)
    print "Result %s" % result
