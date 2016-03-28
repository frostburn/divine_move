from __future__ import division

import json
import os
import random
import subprocess

from django.conf import settings
from django.contrib.auth.forms import UserCreationForm
from django.http import HttpResponse, Http404, HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect, resolve_url
from django.views.generic import RedirectView, View, TemplateView

from tsumego import *


def parse_move(move):
    if move == "pass":
        return 0
    x, y = map(int, move.split("_"))
    return 1 << (x + V_SHIFT * y)


class TsumegoResetView(View):
    def get(self, request):
        return HttpResponse(reset_query())


class TsumegoEmptyView(RedirectView):
    permanent = False
    pattern_name = "tsumego"
    query_string = True
    def get_redirect_url(self, *args, **kwargs):
        base_states = init_query()
        state = base_states[kwargs["name"]].copy()
        state.ko_threats = 0
        kwargs["code"] = state.to_code()
        return super(TsumegoEmptyView, self).get_redirect_url(*args, **kwargs)


class TsumegoView(TemplateView):
    template_name = "tsumego.html"

    def get_context_data(self, *args, **kwargs):
        context = super(TsumegoView, self).get_context_data(*args, **kwargs)
        base_states = init_query()
        state = base_states[kwargs["name"]].from_code(kwargs["code"])
        context["tsumego_name"] = kwargs["name"]
        state_json = state.to_json()
        # state_json["result"] = get_result(state)
        context["state"] = json.dumps(state_json)
        return context


class TsumegoJSONView(View):
    def get(self, request, *args, **kwargs):
        base_states = init_query()
        base_state = base_states[kwargs["name"]]
        try:
            state = base_state.from_code(self.request.GET["code"])
        except TsumegoError as e:
            return JsonResponse({"error": e.message})

        move = self.request.GET.get("move")
        if move:
            # TODO: check that move can be parsed
            valid, prisoners = state.make_move(parse_move(move))
            if not valid:
                return JsonResponse({"error": "Invalid move."})

        add_player = self.request.GET.get("add_player")
        if add_player:
            state.add_player(parse_move(add_player))

        add_opponent = self.request.GET.get("add_opponent")
        if add_opponent:
            state.add_opponent(parse_move(add_opponent))

        remove = self.request.GET.get("remove")
        if remove:
            state.remove(parse_move(remove))

        # Check that the state is still active.
        if self.request.GET.get("vs_book"):
            try:
                make_book_move(state)
            except TsumegoError as e:
                return JsonResponse({"error": e.message})

        result = {}
        if self.request.GET.get("value"):
            value, children = query(state, reverse_target=bool(add_player))
            if not value.valid:
                return JsonResponse({"error": value.error})
            result["value"] = value.to_json()
            # TODO: Add prisoners and make usable by the frontend.
            for move, child in children.items():
                children[move] = child.to_json()
            result["value"]["children"] = children
            result["result"] = format_value(state, value)

        state.fix_targets()
        result.update(state.to_json())

        return JsonResponse(result)
