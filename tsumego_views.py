from __future__ import division

import json
import os
import random
import subprocess

from django.conf import settings
from django.contrib.auth.forms import UserCreationForm
from django.http import HttpResponse, Http404, HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect, resolve_url
from django.views.generic import View, TemplateView

from tsumego import *


def parse_move(move):
    x, y = map(int, move.split("_"))
    return 1 << (x + V_SHIFT * y)


class TsumegoView(TemplateView):
    template_name = "tsumego.html"

    def get_context_data(self, *args, **kwargs):
        context = super(TsumegoView, self).get_context_data(*args, **kwargs)
        base_states = init_query()
        state = base_states[kwargs["name"]].copy()
        context["tsumego_name"] = kwargs["name"]
        context["state"] = json.dumps(state.to_json())
        return context


class TsumegoJSONView(View):
    def get(self, request, *args, **kwargs):
        base_states = init_query()
        base_state = base_states[kwargs["name"]]
        try:
            state = base_state.from_code(self.request.GET["code"])
        except TsumegoError:
            return JsonResponse({"error": "Tsumego not found."})

        move = self.request.GET.get("move")
        if move:
            # TODO: check that move can be parsed
            valid, prisoners = state.make_move(parse_move(move))
            if not valid:
                return JsonResponse({"error": "Invalid move."})
        if self.request.GET.get("vs_book"):
            value, children = query(state)
            if not value.valid:
                return JsonResponse({"error": "Tsumego not in DB."})
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

        return JsonResponse(state.to_json())