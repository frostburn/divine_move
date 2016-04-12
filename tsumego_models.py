# -*- coding: utf-8 -*-
from django.db import models


class TsumegoProblem(models.Model):
    """
    A go problem/puzzle.
    """
    name = models.CharField(max_length=512)
    elo = models.FloatField(default=1500)
    collections = models.ManyToManyField('TsumegoCollection', related_name='problems')
    state_dump = models.CharField(max_length=256)
    archived = models.BooleanField(default=False)

    def __unicode__(self):
        return "%s: %.2f" % (self.name, self.elo)


class TsumegoCollection(models.Model):
    """
    A go problem/puzzle collection.
    """
    name = models.CharField(max_length=512)
    slug = models.SlugField(max_length=128)
    description = models.TextField(default='')

    @classmethod
    def all_to_json(cls):
        result = []
        for collection in cls.objects.order_by("name"):
            result.append({
                "name": collection.name,
                "value": collection.slug,
            })
        return result

    def __unicode__(self):
        return self.name
