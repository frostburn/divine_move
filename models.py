from __future__ import division
from datetime import datetime
from decimal import Decimal

from django.db import models

from go_board import Board
from utils import *


GO_9x9_CODE_LENGTH = 23
GO_9x9_BIN_COUNT = 9 * 9 * 2 + 1


def board_to_code(board):
    return int_to_code(board.to_int(), GO_9x9_CODE_LENGTH)


def code_to_board(code):
    return Board.from_int(code_to_int(code), 9)


class Position(models.Model):
    """
    Abstract game position.
    """
    bins = models.BinaryField()
    heuristic_value = models.FloatField(null=True)
    low_score = models.SmallIntegerField(null=True)
    high_score = models.SmallIntegerField(null=True)

    def get_bins(self):
        bins = bytes(self.bins)
        if not bins:
            return [0] * GO_9x9_BIN_COUNT
        else:
            if bytes is str:
                bins = [ord(c) for c in bins]
            return [bins[2 * i] + 256 * bins[2 * i + 1] for i in xrange(GO_9x9_BIN_COUNT)]

    def set_bins(self, bins):
        if len(bins) != GO_9x9_BIN_COUNT:
            raise ValueError("Invalid bin count")
        if any(b > 65535 for b in bins):
            raise OverflowError("Bin value too large")
        w = 0
        total = 0
        for i, b in enumerate(bins, -81):
            w += i * b
            total += b
        self.heuristic_value = w / total
        bs = []
        for b in bins:
            bs.append(b % 256)
            bs.append(b // 256)
        if bytes is str:
            self.bins = ''.join(chr(b) for b in bs)
        else:
            self.bins = bytes(bs)

    def add_bins(self, bins):
        self.set_bins([a + b for a, b in zip(bins, self.get_bins())])

    def to_json(self):
        return {
            "bins": self.get_bins(),
            "heuristic_value": self.heuristic_value,
            "low_score": self.low_score,
            "high_score": self.high_score,
        }


class State(models.Model):
    """
    Concrete oriented game position.
    """
    code = models.CharField(max_length=GO_9x9_CODE_LENGTH)
    position = models.ForeignKey('Position', related_name='states')

    def __unicode__(self):
        return u"State - %s" % self.code


class PositionInfo(models.Model):
    """
    A move that was played in a game.
    """
    position = models.ForeignKey('Position', related_name='position_infos')
    game_info = models.ForeignKey('GameInfo', related_name='position_infos')
    move_number = models.SmallIntegerField()


def parse_game_info(data):
    for name, field in data.items():
        data[name] = field or ""
    date = data["date"]
    if date:
        if date.count("-") == 2:
            date = datetime.strptime(date, "%Y-%m-%d").date()
        else:
            date = datetime.strptime(date, "%Y").date()
    else:
        date = None
    data["date"] = date
    if data["round"]:
        data["round"] = int(data["round"])
    else:
        data["round"] = None
    if data["handicap"]:
        data["handicap"] = int(data["handicap"])
    else:
        data["handicap"] = None
    if data["time"]:
        data["time"] = int(data["time"])
    else:
        data["time"] = None
    if data["komi"]:
        data["komi"] = Decimal(data["komi"])
    else:
        data["komi"] = None
    return data


class GameInfo(models.Model):
    """
    A game that was played.
    """
    black_player = models.CharField(max_length=64)
    black_rank = models.CharField(max_length=8)
    white_player = models.CharField(max_length=64)
    white_rank = models.CharField(max_length=8)
    result = models.CharField(max_length=8)
    date = models.DateField(null=True)
    event = models.CharField(max_length=64)
    round = models.SmallIntegerField(null=True)
    handicap = models.SmallIntegerField(null=True)
    komi = models.DecimalField(max_digits=4, decimal_places=2, null=True)
    place = models.CharField(max_length=64)
    rules = models.CharField(max_length=32)
    time = models.IntegerField(null=True)
    overtime = models.CharField(max_length=32)
    hash = models.CharField(max_length=32)

    def to_json(self):
        data = {
            "black_player": self.black_player,
            "black_rank": self.black_rank,
            "white_player": self.white_player,
            "white_rank": self.white_rank,
            "result": self.result,
            "date": self.date.strftime("%Y-%m-%d") if self.date else "",
            "event": self.event,
            "round": self.round,
            "handicap": self.handicap,
            "komi": "%.1f" % self.komi if self.komi is not None else "",
            "place": self.place,
            "rules": self.rules,
            "time": self.time,
            "overtime": self.overtime,
            "total_moves": len(self.position_infos.all()),
        }
        for key, value in data.items():
            if value is None:
                data[key] = ""
        return data


class Transition(models.Model):
    """
    Transition between positions.
    """
    source = models.ForeignKey('Position', related_name='transitions')
    target = models.ForeignKey('Position', related_name='parent_transitions')
    times_played = models.IntegerField(default=0)
    ideal_votes = models.IntegerField(default=0)
    good_votes = models.IntegerField(default=0)
    trick_votes = models.IntegerField(default=0)
    bad_votes = models.IntegerField(default=0)
    question_votes = models.IntegerField(default=0)

    def to_json(self, total_continuations):
        likelyhood = self.times_played / total_continuations
        result = {
            "times_played": self.times_played,
            "likelyhood": likelyhood,
            "ideal": self.ideal_votes,
            "good": self.good_votes,
            "trick": self.trick_votes,
            "bad": self.bad_votes,
            "question": self.question_votes,
        }
        color = "#" + 3 * ("%02d" % (99 - 40 * likelyhood))
        labels = self.ideal_votes + self.good_votes + self.trick_votes + self.bad_votes
        if not labels:
            if self.question_votes:
                color = "#0bf"
        else:
            m = max(self.ideal_votes, self.good_votes, self.trick_votes, self.bad_votes)
            if self.ideal_votes == m:
                color = "#070"
            elif self.good_votes == m:
                color = "#560"
            elif self.bad_votes == m:
                color = "#a33"
            else:
                color = "#de0"
        result["color"] = color
        return result


def create_position(code):
    board = Board.from_int(code_to_int(code), 9)
    codes = [code]
    for sister in board.sisters():
        codes.append(int_to_code(sister.to_int(), GO_9x9_CODE_LENGTH))
    position = Position.objects.create()
    for code in codes:
        State.objects.create(code=code, position=position)
    return position


def get_or_create_position(code):
    state = State.objects.filter(code=code)
    if state.exists():
        return state.first().position, False
    else:
        return create_position(code), True