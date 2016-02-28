# -*- coding: utf-8 -*-


ALPHA = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
HUMAN_ALPHA = "ABCDEFGHJKLMNOPQRSTUVWXYZ"


def popcount(b):
    if b >= (1 << 64):
        return popcount(b & 0xFFFFFFFFFFFFFFFF) + popcount(b >> 64)
    b = (b & 0x5555555555555555) + (b >> 1 & 0x5555555555555555)
    b = (b & 0x3333333333333333) + (b >> 2 & 0x3333333333333333)
    b = b + (b >> 4) & 0x0F0F0F0F0F0F0F0F
    b = b + (b >> 8)
    b = b + (b >> 16)
    b = b + (b >> 32) & 0x0000007F
    return b


def mirror_v(b, v_shift):
    r = 0
    mask = 0
    for x in xrange(v_shift - 1):
        mask |= 1 << x
    for y in xrange(v_shift - 1):
        r |= ((b >> (y * v_shift)) & mask) << ((v_shift - 2 - y) * v_shift)
    return r


def mirror_h(b, v_shift):
    r = 0
    mask = 0
    for y in xrange(v_shift - 1):
        mask |= 1 << (y * v_shift)
    for x in xrange(v_shift - 1):
        r |= ((b >> x) & mask) << (v_shift - 2 - x)
    return r


def rotate(b, v_shift):
    r = 0
    for x in xrange(v_shift - 1):
        for y in xrange(v_shift - 1):
            if b & (1 << (x + y * v_shift)):
                r |= 1 << (y + (v_shift - 2 - x) * v_shift)
    return r

_h0 = 0
_h1 = 0
_v0 = 0
_v1 = 0
for y in xrange(9):
    for x in xrange(9):
        if x % 3 == 0:
            _h0 |= 1 << (x + 10 * y)
            _v0 |= 1 << (y + 10 * x)
        if (x // 3) % 3 == 0:
            _h1 |= 1 << (x + 10 * y)
            _v1 |= 1 << (y + 10 * x)
_h0m = _h0 << 1
_v0m = _v0 << 10
_h1m = _h1 << 3
_v1m = _v1 << 30


def mirror_h9(b):
    b = ((b >> 2) & _h0) | ((b & _h0) << 2) | (b & _h0m)
    return ((b >> 6) & _h1) | ((b & _h1) << 6) | (b & _h1m)


def mirror_v9(b):
    b = ((b >> 20) & _v0) | ((b & _v0) << 20) | (b & _v0m)
    return (b >> 60) | ((b & _v1) << 60) | (b & _v1m)


_d = [0] * 17
for y in xrange(9):
    for x in xrange(9):
        p = 1 << (x + 10 * y)
        z = x + y
        for i in xrange(17):
            if z == i:
                _d[i] |= p

# TODO: Use recursive 3x3 flips or some kind of XOR thingy
def mirror_d9(b):
    r = b & _d[8]
    for i in range(8):
        j = 8 - i
        r |= (b & _d[i]) << (11 * j)
        r |= (b & _d[16 - i]) >> (11 * j)
    return r


ko_v9 = {0: 0}
ko_h9 = {0: 0}
ko_d9 = {0: 0}

for y in xrange(9):
    for x in xrange(9):
        ko = 1 << (x + 10 * y)
        ko_v9[ko] = mirror_v9(ko)
        ko_h9[ko] = mirror_h9(ko)
        ko_d9[ko] = mirror_d9(ko)


_ht0 = 0
_ht1 = 0
_ht2 = 0
_ht3 = 0
_vt0 = 0
_vt1 = 0
_vt2 = 0
_vt3 = 0
for y in xrange(13):
    _ht0 |= 1 << (6 + 14 * y)
    _vt0 |= 1 << (y + 84)
    for x in xrange(6):
        if x % 3 == 0:
            _ht1 |= 1 << (x + 14 * y)
            _ht1 |= 1 << (x + 7 + 14 * y)
            _vt1 |= 1 << (y + 14 * x)
            _vt1 |= 1 << (y + 14 * x + 98)
        if (x // 3) % 2 == 0:
            _ht2 |= 1 << (x + 14 * y)
            _ht2 |= 1 << (x + 7 + 14 * y)
            _vt2 |= 1 << (y + 14 * x)
            _vt2 |= 1 << (y + 14 * x + 98)
        _ht3 |= 1 << (x + 14 * y)
        _vt3 |= 1 << (y + 14 * x)
_ht1m = _ht1 << 1
_vt1m = _vt1 << 14


def mirror_h13(b):
    m = b & _ht0
    b = ((b >> 2) & _ht1) | ((b & _ht1) << 2) | (b & _ht1m)
    b = ((b >> 3) & _ht2) | ((b & _ht2) << 3)
    b = ((b >> 7) & _ht3) | ((b & _ht3) << 7)
    return m | b


def mirror_v13(b):
    m = b & _vt0
    b = ((b >> 28) & _vt1) | ((b & _vt1) << 28) | (b & _vt1m)
    b = ((b >> 42) & _vt2) | ((b & _vt2) << 42)
    b = (b >> 98) | ((b & _vt3) << 98)
    return m | b


_dt = [0] * 25
for y in xrange(13):
    for x in xrange(13):
        p = 1 << (x + 14 * y)
        z = x + y
        for i in xrange(25):
            if z == i:
                _dt[i] |= p


def mirror_d13(b):
    r = b & _dt[12]
    for i in range(12):
        j = 12 - i
        r |= (b & _dt[i]) << (15 * j)
        r |= (b & _dt[24 - i]) >> (15 * j)
    return r


ko_v13 = {0: 0}
ko_h13 = {0: 0}
ko_d13 = {0: 0}

for y in xrange(13):
    for x in xrange(13):
        ko = 1 << (x + 14 * y)
        ko_v13[ko] = mirror_v13(ko)
        ko_h13[ko] = mirror_h13(ko)
        ko_d13[ko] = mirror_d13(ko)


def flood(source, target, v_shift):
    source &= target
    if not source:
        return 0
    while True:
        temp = source
        source |= (
            (source >> 1) |
            (source << 1) |
            (source >> v_shift) |
            (source << v_shift)
        ) & target
        if temp == source:
            break
    return source


def chains(b, v_shift):
    result = []
    y = 0
    while b:
        for x in range(0, v_shift - 1, 2):
            chain = flood(3 << (x + y * v_shift), b, v_shift)
            if chain:
                result.append(chain)
                b ^= chain
        y += 1
    return result


def liberties(b, e, v_shift):
    l = (b >> 1) | (b << 1) | (b >> v_shift) | (b << v_shift)
    return l & ~b & e


class Board(object):
    def __init__(self, size, copying=False):
        assert size == 9 or size == 13
        self.size = size
        self.v_shift = size + 1
        self.playing_area = 0
        if not copying:
            for x in xrange(size):
                for y in xrange(size):
                    self.playing_area |= 1 << (x + y * self.v_shift)
        self.player = 0
        self.opponent = 0
        self.ko = 0
        self.passes = 0
        self.black_to_play = True

    def __eq__(self, other):
        return (
            self.size == other.size and\
            self.player == other.player and\
            self.opponent == other.opponent and\
            self.ko == other.ko and\
            self.passes == other.passes and\
            self.black_to_play == other.black_to_play
        )

    def __ne__(self, other):
        return not self.__eq__(other)

    def make_move(self, x, y=None, check=False):
        if check:
            old_player = self.player
            old_opponent = self.opponent
            old_ko = self.ko
        if y is None:
            y = x // self.size
            x = x % self.size
        if x >= self.size or y >= self.size:
            self.pass_()
            return
        move = 1 << (x + y * self.v_shift)
        legal = not ((self.player | self.opponent | self.ko) & move)
        if not legal:
            if check:
                return False
            else:
                assert False
        self.player |= move
        kill = 0
        chains_in_danger = [
            flood(move << 1, self.opponent, self.v_shift),
            flood(move >> 1, self.opponent, self.v_shift),
            flood(move << self.v_shift, self.opponent, self.v_shift),
            flood(move >> self.v_shift, self.opponent, self.v_shift)
        ]
        for chain in chains_in_danger:
            if not chain:
                continue
            if not liberties(chain, self.playing_area & ~self.player, self.v_shift):
                kill |= chain
        self.opponent ^= kill
        self.ko = 0
        if popcount(kill) == 1:
            if not liberties(move, self.player, self.v_shift):
                if liberties(move, self.playing_area & ~self.opponent, self.v_shift) == kill:
                    self.ko = kill
        chain = flood(move, self.player, self.v_shift)
        legal = liberties(chain, self.playing_area & ~self.opponent, self.v_shift)
        if not legal:
            if check:
                self.player = old_player
                self.opponent = old_opponent
                self.ko = old_ko
                return False
            else:
                assert False
        self.swap_turns()
        self.passes = 0
        if check:
            return True

    def swap_turns(self):
        self.player, self.opponent = self.opponent, self.player
        self.black_to_play = not self.black_to_play

    def pass_(self):
        self.swap_turns()
        # Clearing a ko doesn't count as a pass towards ending the game.
        if self.ko:
            self.ko = 0
        else:
            self.passes += 1

    def mirror_v(self):
        if self.size == 9:
            self.player = mirror_v9(self.player)
            self.opponent = mirror_v9(self.opponent)
            self.ko = ko_v9[self.ko]
        elif self.size == 13:
            self.player = mirror_v13(self.player)
            self.opponent = mirror_v13(self.opponent)
            self.ko = ko_v13[self.ko]

    def mirror_h(self):
        if self.size == 9:
            self.player = mirror_h9(self.player)
            self.opponent = mirror_h9(self.opponent)
            self.ko = ko_h9[self.ko]
        elif self.size == 13:
            self.player = mirror_h13(self.player)
            self.opponent = mirror_h13(self.opponent)
            self.ko = ko_v13[self.ko]

    def mirror_d(self):
        if self.size == 9:
            self.player = mirror_d9(self.player)
            self.opponent = mirror_d9(self.opponent)
            self.ko = ko_d9[self.ko]
        elif self.size == 13:
            self.player = mirror_d13(self.player)
            self.opponent = mirror_d13(self.opponent)
            self.ko = ko_d13[self.ko]

    def copy(self):
        c = Board(self.size, copying=True)
        c.playing_area = self.playing_area
        c.player = self.player
        c.opponent = self.opponent
        c.ko = self.ko
        c.black_to_play = self.black_to_play
        c.passes = self.passes
        return c

    def key(self):
        return (self.size, self.player, self.opponent, self.ko, self.passes, self.black_to_play)

    def light_key(self):
        return (self.player, self.opponent, self.ko)

    def canonical_light_key(self):
        keys = []
        temp = self.copy()
        temp.black_to_play = True
        keys.append(temp.light_key())
        temp.mirror_v()
        keys.append(temp.light_key())
        temp.mirror_h()
        keys.append(temp.light_key())
        temp.mirror_v()
        keys.append(temp.light_key())
        temp.mirror_d()
        keys.append(temp.light_key())
        temp.mirror_v()
        keys.append(temp.light_key())
        temp.mirror_h()
        keys.append(temp.light_key())
        temp.mirror_v()
        keys.append(temp.light_key())
        return min(keys)

    def sisters(self):
        seen = set()
        sisters = []
        temp = self.copy()
        seen.add(temp.light_key())
        temp.mirror_v()
        key = temp.light_key()
        if key not in seen:
            sisters.append(temp)
            temp = temp.copy()
            seen.add(key)
        temp.mirror_h()
        key = temp.light_key()
        if key not in seen:
            sisters.append(temp)
            temp = temp.copy()
            seen.add(key)
        temp.mirror_v()
        key = temp.light_key()
        if key not in seen:
            sisters.append(temp)
            temp = temp.copy()
            seen.add(key)
        temp.mirror_d()
        key = temp.light_key()
        if key not in seen:
            sisters.append(temp)
            temp = temp.copy()
            seen.add(key)
        temp.mirror_v()
        key = temp.light_key()
        if key not in seen:
            sisters.append(temp)
            temp = temp.copy()
            seen.add(key)
        temp.mirror_h()
        key = temp.light_key()
        if key not in seen:
            sisters.append(temp)
            temp = temp.copy()
            seen.add(key)
        temp.mirror_v()
        key = temp.light_key()
        if key not in seen:
            sisters.append(temp)
        return sisters

    def children(self, separate_unique=True):
        if self.passes >= 2:
            if separate_unique:
                return [], []
            else:
                return []
        has_symmetries = False
        if separate_unique:
            has_symmetries = len(self.sisters()) < 8
        unique_children = []
        redundant_children = []
        seen = set()
        empty = not self.player and not self.opponent
        for y in xrange(self.size):
            yy = y
            for x in xrange(self.size):
                if empty:
                    x, y = self.size - 1 - yy, x
                coord = "%s%d" % (ALPHA[x], y)
                child = self.copy()
                if child.make_move(x, y, True):
                    if separate_unique and has_symmetries:
                        key = child.canonical_light_key()
                        if key not in seen:
                            seen.add(key)
                            unique_children.append((coord, child))
                        else:
                            redundant_children.append((coord, child))
                    else:
                        unique_children.append((coord, child))
        child = self.copy()
        child.pass_()
        unique_children.append(("pass", child))
        if separate_unique:
            return unique_children, redundant_children
        else:
            return unique_children

    def score(self):
        """
        Try to score the position.
        """
        player = self.player
        opponent = self.opponent
        # Fill all controlled regions.
        for region in chains(self.playing_area & ~player, self.v_shift):
            if not (region & opponent):
                player |= region
        for region in chains(self.playing_area & ~opponent, self.v_shift):
            if not (region & player):
                opponent |= region

        # Count stones and their liberties towards the score.
        player_score = popcount(player | liberties(player, self.playing_area & ~opponent, self.v_shift))
        opponent_score = popcount(opponent | liberties(opponent, self.playing_area & ~player, self.v_shift))
        # Ignore self.black_to_play, assume we're negamaxing.
        return player_score - opponent_score

    def render(self):
        if self.black_to_play:
            black = self.player
            white = self.opponent
        else:
            black = self.opponent
            white = self.player
        r = u""
        for y in xrange(self.size):
            r += u"\x1b[0;30;43m%s" % ((self.size - y) % 10)  # Yellow bg
            for x in xrange(self.size):
                m = 1 << (x + y * self.v_shift)
                if black & m:
                    r += u"\x1b[30m● "
                elif white & m:
                    r += u"\x1b[37m● "
                elif self.ko & m:
                    r += u"\x1b[30m□ "
                else:
                    r += u"  ";
            r += u"\x1b[0m\n"
        r += u" "
        for x in xrange(self.size):
            r += HUMAN_ALPHA[x] + u" "
        r += u"\n"
        if self.black_to_play:
            r += u"Black to play"
        else:
            r += u"White to play"
        r += u", passes=%d" % self.passes
        return r

    def to_json(self):
        result = {
            "player": [],
            "opponent": [],
            "ko": [],
            "passes": self.passes,
            # black_to_play unserialized
        }
        for y in xrange(self.size):
            for x in xrange(self.size):
                coord = "%s%d" % (ALPHA[x], y)
                m = 1 << (x + y * self.v_shift)
                if self.player & m:
                    result["player"].append(coord)
                elif self.opponent & m:
                    result["opponent"].append(coord)
                elif self.ko & m:
                    result["ko"].append(coord)
        return result

    @classmethod
    def from_json(cls, data):
        board = cls(9)
        board.passes = data["passes"]
        for coord in data["player"]:
            x = ALPHA.index(coord[0])
            y = int(coord[1:])
            m = 1 << (x + y * board.v_shift)
            board.player |= m
        for coord in data["opponent"]:
            x = ALPHA.index(coord[0])
            y = int(coord[1:])
            m = 1 << (x + y * board.v_shift)
            board.opponent |= m
        for coord in data["ko"]:
            x = ALPHA.index(coord[0])
            y = int(coord[1:])
            m = 1 << (x + y * board.v_shift)
            board.ko |= m
        return board

    def to_int(self):
        code = 0
        i = 0
        ko_pos = 0
        for y in xrange(self.size):
            for x in xrange(self.size):
                code *= 3
                m = 1 << (x + y * self.v_shift)
                if self.player & m:
                    code += 1
                elif self.opponent & m:
                    code += 2
                if self.ko & m:
                    ko_pos = i
                i += 1
        if not self.ko:
            ko_pos = self.size ** 2
        if self.passes:
            assert not self.ko
            assert self.passes <= 2
            ko_pos += self.passes
        code *= 3 + self.size ** 2
        code += ko_pos

        return code

    @classmethod
    def from_int(cls, code, size):
        board = cls(size)
        ko_pos = code % (3 + size ** 2)
        code //= (3 + size ** 2)
        if ko_pos < size ** 2:
            x = ko_pos % size
            y = ko_pos // size
            board.ko = 1 << (x + y * board.v_shift)
        else:
            board.passes = ko_pos - size ** 2
        for y in reversed(xrange(size)):
            for x in reversed(xrange(size)):
                m = 1 << (x + y * board.v_shift)
                stone = code % 3
                code //= 3
                if stone == 1:
                    board.player |= m
                elif stone == 2:
                    board.opponent |= m
        return board


def get_orientation(a, b):
    if a == b:
        return "none"
    c = a.copy()
    c.mirror_v()
    if c == b:
        return "mirror_v"
    c.mirror_h()
    if c == b:
        return "mirror_hv"
    c.mirror_v()
    if c == b:
        return "mirror_h"
    c.mirror_d()
    if c == b:
        return "mirror_dv"
    c.mirror_v()
    if c == b:
        return "mirror_d"
    c.mirror_h()
    if c == b:
        return "mirror_dh"
    c.mirror_v()
    if c == b:
        return "mirror_dhv"
    raise ValueError("Non-orientable arguments")
