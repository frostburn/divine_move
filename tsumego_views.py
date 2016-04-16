# -*- coding: utf-8 -*-
from __future__ import division

import json
import os
import random
import re
import subprocess

from django.conf import settings
from django.contrib.auth.forms import UserCreationForm
from django.core.urlresolvers import reverse
from django.utils.decorators import method_decorator
from django.utils.text import slugify
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from django.http import HttpResponse, Http404, HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect, resolve_url
from django.views.generic import RedirectView, View, TemplateView

from tsumego import *
from models import UserProfile, TsumegoProblem, TsumegoCollection, name_key
from utils import elo_update


def parse_move(move):
    if move == "pass":
        return 0
    x, y = map(int, move.split("_"))
    return 1 << (x + V_SHIFT * y)


def process_for_base_state(state):
    base_states = init_query()
    for name, base_state in base_states.items():
        is_sub_state, colors_match = base_state.has_sub_state(state)
        if is_sub_state:
            break
    else:
        return None
    if (base_state.white_to_play == state.white_to_play) ^ colors_match:
        state.min_ko_threats = -base_state.max_ko_threats
        state.max_ko_threats = -base_state.min_ko_threats
    else:
        state.min_ko_threats = base_state.min_ko_threats
        state.max_ko_threats = base_state.max_ko_threats
    state.colors_match = colors_match

    return name


def get_state_json(state, name, problem_mode=False):
    url_code = state.to_url_code()
    state_json = state.to_json()
    if problem_mode:
        title = get_goal(state)
    else:
        title = "White to play" if state.white_to_play else "Black to play"
        if not state.active:
            title = ""
    state_json["title"] = title
    state_json["url_code"] = url_code
    state_json["tsumego_url"] = reverse("tsumego", kwargs={"name": name, "code": url_code})
    problem = TsumegoProblem.objects.filter(state_dump=state_json["dump"]).first()
    if problem is None:
        state_json["problem_name"] = None
        state_json["problem_collections"] = []
    else:
        state_json["problem_name"] = problem.name
        state_json["problem_collections"] = [collection.slug for collection in problem.collections.all()]
    return state_json


def get_problem_url(problem):
    base_states = init_query()
    state = State.load(problem.state_dump)
    if not state.legal:
        return None
    name = process_for_base_state(state)
    if name is None:
        return None
    url_code = state.to_url_code()
    if url_code is None:
        return None
    return reverse("tsumego_problem", kwargs={"name": name, "code": url_code})


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
    problem_mode = False

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
        state.colors_match = True
        if swap_colors:
            state.white_to_play = not state.white_to_play
        if settings.LOCAL_DEBUG:
            print state.render()
            print state.dump()
        if not state.legal:
            raise Http404("Illegal position.")
        ko_threats = self.request.GET.get("ko_threats")
        if ko_threats is not None:
            ko_threats = int(ko_threats)
            if not (state.min_ko_threats <= ko_threats <= state.max_ko_threats):
                raise Http404("Tsumego not found. Too many ko threats.")
            state.ko_threats = ko_threats
        context["problem_options"] = json.dumps(TsumegoCollection.all_to_json())
        context["problem_mode"] = json.dumps(self.problem_mode)
        state_json = get_state_json(state, kwargs["name"], self.problem_mode)
        context["state"] = json.dumps(state_json)
        return context


class TsumegoProblemView(TsumegoView):
    problem_mode = True


class TsumegoProblemIndexView(TemplateView):
    template_name = "tsumego_problem_index.html"

    def get_context_data(self, *args, **kwargs):
        context = super(TsumegoProblemIndexView, self).get_context_data(*args, **kwargs)

        # Hello! I'm a duck!
        class Uncategorized(object):
            name = "Uncategorized"
            problems = TsumegoProblem.objects.filter(collections=None)

        collections = []
        tsumego_collections = sorted(TsumegoCollection.objects.all(), key=name_key)
        tsumego_collections.append(Uncategorized)  # Who's a good duck? You are, yes you are!
        for collection in tsumego_collections:
            problems = []
            for problem in sorted(collection.problems.filter(archived=False), key=name_key):
                url = get_problem_url(problem)
                if url is None:
                    # The base state has gone missing.
                    continue
                problems.append({
                    "name": problem.name,
                    "url": url,
                })
            collections.append({
                "name": collection.name,
                "problems": problems,
            })
        context["collections"] = collections
        return context

    def post(self, request, *args, **kwargs):
        name = request.POST["name"]
        slug = slugify(name)
        collection = TsumegoCollection.objects.create(name=name, slug=slug)
        collection.save()
        return self.get(request, *args, **kwargs)


class TsumegoJSONView(View):
    def get(self, request, *args, **kwargs):
        init_query()
        state = State.load(self.request.GET["dump"])
        state.captures_by_player, state.captures_by_opponent = map(int, self.request.GET["captures"].split("_"))

        if settings.LOCAL_DEBUG:
            print state.render()
            print state.dump()

        srg = self.request.GET.get

        result = {}

        if not state.legal:
            return JsonResponse({"error": "Illegal position"})

        # Soft manipulation before processing for base state.
        if srg("swap"):
            state.swap_players()
            state.ko = 0  # Any ko would be in an illegal position so it has to be cleared.

        if srg("color"):
            state.white_to_play = not state.white_to_play

        name = process_for_base_state(state)

        ko_threats = srg("ko_threats")
        if ko_threats:
            # query() will check if this is valid or not.
            state.ko_threats = int(ko_threats)

        if srg("problem"):
            goal_value, children = query(state)

        move = srg("move")
        if move:
            move = parse_move(move)
            valid, prisoners = state.make_move(move)
            if not valid:
                return JsonResponse({"error": "Invalid move."})

            if srg("problem"):
                achieved_value = children[move]
                result["problem_failed"] = not goal_value.achieves_goal(achieved_value, prisoners)
                if result.get("problem_failed"):
                    result["title"] = "Failed"

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
                if srg("problem") and not state.active and not result.get("problem_failed"):
                    result["problem_solved"] = True
                    result["title"] = "Correct"
            except TsumegoError as e:
                return JsonResponse({"error": e.message})

        include_value = srg("value") or not state.active;
        if include_value:
            try:
                value, children = query(state, reverse_target=bool(add_player))
            except TsumegoError as e:
                return JsonResponse({"error": e.message})
            result["value"] = value.to_json()

        if include_value:
            child_results = []
            for move, child_value in children.items():
                child = state.copy()
                valid, prisoners = child.make_move(move)
                assert valid
                child_results.append([
                    to_coords(move),
                    format_value(child, child_value, low=False),
                    value.low_child(child_value, prisoners),
                    child_value.to_json(),
                ])
            result["value"]["children"] = child_results
            result["result"] = format_value(state, value)

        state.fix_targets()

        # Not passing srg("problem") here because the title isn't dynamically updated.
        state_json = get_state_json(state, name)
        state_json.update(result)

        return JsonResponse(state_json)

    @method_decorator(csrf_exempt)  # TOFIX: How about no
    def dispatch(self, *args, **kwargs):
        return super(TsumegoJSONView, self).dispatch(*args, **kwargs)

    def _add_problem(self, data):
        problem, created = TsumegoProblem.objects.get_or_create(state_dump=data["dump"])
        name = data["name"]
        if not name:
            problem.archived = True
            if created:
                return {"error": "Please enter a name."}
        else:
            problem.name = name
            problem.archived = False
        problem.collections = TsumegoCollection.objects.filter(slug__in=data["collections"])
        problem.save()
        verb = "created" if created else "updated"
        if problem.archived:
            verb = "archived"
        msg = "Problem {} successfully.".format(verb)
        return {"success": msg}

    def _get_user_elo(self, request):
        if request.user.is_anonymous():
            try:
                return float(request.session.get("elo"))
            except (ValueError, TypeError):
                return 1500.0
        else:
            profile, created = UserProfile.objects.get_or_create(user=request.user)
            return profile.elo

    def _set_user_elo(self, request, elo, problem):
        if request.user.is_anonymous():
            request.session["elo"] = elo
        else:
            profile, created = UserProfile.objects.get_or_create(user=request.user)
            profile.elo = elo
            profile.save()

    def _make_solver(self, request, problem):
        # TODO: Convert sessions to user profiles upon signup.
        if request.user.is_anonymous():
            problem_ids = request.session.get("problem_ids", [])
            if problem.id not in problem_ids:
                problem_ids.append(problem.id)
                request.session["problem_ids"] = problem_ids
                return True
        else:
            profile, created = UserProfile.objects.get_or_create(user=request.user)
            if not profile.tried_problems.filter(pk=problem.pk).exists():
                profile.tried_problems.add(problem)
                profile.save()
                return True
        return False

    def _update_elo(self, request, data):
        user_elo = self._get_user_elo(request)
        problem = TsumegoProblem.objects.get(state_dump=data["dump"])
        user_delta = 0
        problem_delta = 0
        if self._make_solver(request, problem):
            result = 1.0 if data["success"] else 0.0
            user_delta = elo_update(user_elo, problem.elo, result, k_factor=32.0)
            problem_delta = elo_update(problem.elo, user_elo, 1.0 - result, k_factor=16.0)
            user_elo += user_delta
            problem.elo += problem_delta
            problem.save()
            self._set_user_elo(request, user_elo, problem)
        two_decimals = "{:.2f}"
        return {
            "user_elo": two_decimals.format(user_elo),
            "user_delta": format_delta(user_delta),
            "problem_name": problem.name,
            "problem_elo": two_decimals.format(problem.elo),
            "problem_delta": format_delta(problem_delta),
        }

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        if data["action"] == "add_problem":
            result = self._add_problem(data)
        elif data["action"] == "update_elo":
            result = self._update_elo(request, data)
        else:
            raise ValueError("Invalid action")
        return JsonResponse(result)
