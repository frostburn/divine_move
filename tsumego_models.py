# -*- coding: utf-8 -*-
import re

from django.contrib.auth.models import User
from django.db import models

from tsumego import State


def name_key(obj):
    result = []
    for part in filter(None, re.split("(\d+)", obj.name)):
        if part.isdigit():
            part = int(part)
        result.append(part)
    return result


class UserProfile(models.Model):
    user = models.OneToOneField(User, related_name='profile')
    elo = models.FloatField(default=1500)
    tried_problems = models.ManyToManyField('TsumegoProblem', related_name='solvers')


class TsumegoProblem(models.Model):
    """
    A go problem/puzzle.
    """
    name = models.CharField(max_length=512)
    elo = models.FloatField(default=1500)
    collections = models.ManyToManyField('TsumegoCollection', related_name='problems')
    state_dump = models.CharField(max_length=256)
    archived = models.BooleanField(default=False)

    _state_obj = None

    @property
    def state(self):
        if self._state_obj is None:
            self._state_obj = State.load(self.state_dump)
        return self._state_obj

    def __unicode__(self):
        return "%s: %.2f" % (self.name, self.elo)


class TsumegoCollection(models.Model):
    """
    A go problem/puzzle collection.
    """
    name = models.CharField(max_length=512)
    slug = models.SlugField(max_length=128, unique=True)
    description = models.TextField(default='')

    @classmethod
    def all_to_json(cls):
        result = []
        for collection in sorted(cls.objects.all(), key=name_key):
            result.append({
                "name": collection.name,
                "value": collection.slug,
            })
        return result

    def __unicode__(self):
        return self.name
