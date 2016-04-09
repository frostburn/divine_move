# -*- coding: utf-8 -*-
from __future__ import division

import json
import os
import random
import subprocess

from django.conf import settings
from django.contrib.auth.forms import UserCreationForm
from django.core.urlresolvers import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from django.http import HttpResponse, Http404, HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect, resolve_url
from django.views.generic import RedirectView, View, TemplateView

from tsumego import *
from models import TsumegoProblem


def parse_move(move):
    if move == "pass":
        return 0
    x, y = map(int, move.split("_"))
    return 1 << (x + V_SHIFT * y)


def get_state_json(state, name):
    state_json = state.to_json()
    state_json["tsumego_url"] = reverse('tsumego', kwargs={'name': name, 'code': state_json["code"]})
    return state_json


class TsumegoResetView(View):
    def get(self, request):
        return HttpResponse(reset_query())


class TsumegoIndexView(View):
    def get(self, request, *args, **kwargs):
        base_states = init_query()
        content = '<html><body>'
        for name in sorted(base_states.keys()):
            content += '<a href="' + reverse('tsumego_empty', kwargs={'name': name}) + '">' + name + '</a><br>'
            if settings.LOCAL_DEBUG:
                print base_states[name].render()
        content += '</body></html>'
        return HttpResponse(content)


class TsumegoEmptyView(RedirectView):
    permanent = False
    pattern_name = "tsumego"
    query_string = True
    def get_redirect_url(self, *args, **kwargs):
        base_states = init_query()
        state = base_states[kwargs["name"]].copy()
        state.empty()
        kwargs["code"] = state.to_code()
        return super(TsumegoEmptyView, self).get_redirect_url(*args, **kwargs)


class TsumegoView(TemplateView):
    template_name = "tsumego.html"

    def get_context_data(self, *args, **kwargs):
        context = super(TsumegoView, self).get_context_data(*args, **kwargs)
        base_states = init_query()
        base_state = base_states.get(kwargs["name"])
        if not base_state:
            raise Http404("Tsumego not found.")
        code = kwargs["code"]
        swap_colors = code.startswith("_")
        code = code.lstrip("_")
        state = base_state.from_code(code)
        state.white_to_play ^= swap_colors
        ko_threats = self.request.GET.get("ko_threats")
        if ko_threats is not None:
            ko_threats = int(ko_threats)
            if not (state.min_ko_threats <= ko_threats <= state.max_ko_threats):
                raise Http404("Tsumego not found. Too many ko threats.")
            state.ko_threats = ko_threats
        context["tsumego_name"] = kwargs["name"]
        context["swap_colors"] = json.dumps(swap_colors)
        state_json = get_state_json(state, kwargs["name"])
        state_json["code"] = code
        context["state"] = json.dumps(state_json)
        return context


class TsumegoProblemIndexView(View):
    def get(self, request, *args, **kwargs):
        base_states = init_query()
        content = '<html><body>'
        for problem in TsumegoProblem.objects.all():
            state = State.load(problem.state_dump)
            for name, base_state in base_states.items():
                is_sub_state, colors_match = base_state.has_sub_state(state)
                if is_sub_state:
                    break
            else:
                content += problem.name + '<br>'
                continue
            if not colors_match:
                state.white_to_play = not state.white_to_play
            code = state.to_code()
            if not colors_match:
                code = '_' + code
            content += '<a href="' + reverse('tsumego', kwargs={'name': name, 'code': code}) + '">' + problem.name + '</a><br>'
            if settings.LOCAL_DEBUG:
                print state.render()
        content += '</body></html>'
        return HttpResponse(content)


class TsumegoJSONView(View):
    def get(self, request, *args, **kwargs):
        base_states = init_query()
        base_state = base_states[kwargs["name"]]
        try:
            state = base_state.from_code(self.request.GET["code"])
        except TsumegoError as e:
            return JsonResponse({"error": e.message})

        srg = self.request.GET.get

        dump = srg("dump")
        if dump:
            try:
                state.update(dump)
            except TsumegoError as e:
                return JsonResponse({"error": e.message})

        ko_threats = srg("ko_threats")
        if ko_threats:
            ko_threats = int(ko_threats)
            if not (state.min_ko_threats <= ko_threats <= state.max_ko_threats):
                return JsonResponse({"error": "Invalid ko threats"})
            state.ko_threats = ko_threats

        move = srg("move")
        if move:
            # TODO: check that move can be parsed
            valid, prisoners = state.make_move(parse_move(move))
            if not valid:
                return JsonResponse({"error": "Invalid move."})

        add_player = srg("add_player")
        if add_player:
            state.add_player(parse_move(add_player))

        add_opponent = srg("add_opponent")
        if add_opponent:
            state.add_opponent(parse_move(add_opponent))

        remove = srg("remove")
        if remove:
            state.remove(parse_move(remove))

        if srg("book"):
            try:
                make_book_move(state, low=True)
            except TsumegoError as e:
                return JsonResponse({"error": e.message})

        if srg("vs_book"):
            try:
                make_book_move(state)
            except TsumegoError as e:
                return JsonResponse({"error": e.message})

        if srg("swap"):
            state.swap_players()

        result = {}
        include_value = srg("value") or not state.active;
        if include_value:
            value, children = query(state, reverse_target=bool(add_player))
            if not value.valid:
                return JsonResponse({"error": value.error})
            result["value"] = value.to_json()

        # All the queries have to be done prior to color swapping.
        if srg("color"):
            state.white_to_play = not state.white_to_play

        if include_value:
            child_results = []
            for move, child_value in children.items():
                child = state.copy()
                valid, prisoners = child.make_move(move)
                assert valid
                child_results.append([
                    to_coords(move),
                    format_value(child,child_value),
                    value.low_child(child_value, prisoners),
                ])
            result["value"]["children"] = child_results
            result["result"] = format_value(state, value)

        state.fix_targets()

        if settings.LOCAL_DEBUG:
            print state.render()

        result.update(get_state_json(state, kwargs["name"]))

        # The white_to_play bit is used when decoding so we have do some shuffling here.
        if srg("color"):
            state.white_to_play = not state.white_to_play
            result["code"] = state.to_code()

        return JsonResponse(result)

    @method_decorator(csrf_exempt)  # TOFIX: How about no
    def dispatch(self, *args, **kwargs):
        return super(TsumegoJSONView, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        if data["action"] == "add_problem":
            problem, created = TsumegoProblem.objects.get_or_create(state_dump=data["dump"])
            problem.name = data["name"]
            problem.save()
        else:
            raise ValueError("Invalid action")
        return JsonResponse({"success": True})
