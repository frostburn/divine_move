# -*- coding: utf-8 -*-
from django.db import models


class TsumegoProblem(models.Model):
    """
    A go problem/puzzle.
    """
    name = models.CharField(max_length=512)
    elo = models.FloatField(default=1500)
    # collections = models.ManyToManyField('Collection', related_name='problems')
    state_dump = models.CharField(max_length=256)


# class Collection(models.Model):
#     """
#     A go problem/puzzle collection.
#     """
#     name = models.CharField(max_length=512)
#     slug = models.SlugField(max_length=128)
