from __future__ import division

import json
import os
import subprocess

from django.conf import settings
from django.contrib.auth.forms import UserCreationForm
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import redirect, resolve_url
from django.views.generic import View, RedirectView, TemplateView
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
from django.template.response import TemplateResponse
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import is_safe_url
from django.contrib.auth import REDIRECT_FIELD_NAME, authenticate, login as auth_login, logout as auth_logout
from django.utils.safestring import mark_safe

from ipware.ip import get_ip

from utils import *
from chess_data import low_endgames, high_endgames
from models import *
from go_board import Board
from sgf import process_sgf


def clear_session(request):
    request.session.flush()
    return HttpResponse("Session cleared")


def logout(request):
    auth_logout(request)
    return TemplateResponse(request, 'registration/site_logged_out.html')


class CompleteUserCreationForm(UserCreationForm):
    class Meta:
        model = UserCreationForm.Meta.model
        fields = ("username", "email", "first_name", "last_name")


def _create_user_profile(request, user):
    profile = UserProfile.objects.create(user=user)
    profile.elo = request.session.get("elo", 1500.0)
    for problem in TsumegoProblem.objects.filter(pk__in=request.session.get("problem_ids", [])):
        profile.tried_problems.add(problem)
    profile.save()


def signup(
        request,
        template_name='registration/signup.html',
        redirect_field_name=REDIRECT_FIELD_NAME,
        user_creation_form=CompleteUserCreationForm,
        current_app=None,
        extra_context=None
    ):
    """
    Displays the signup form and handles the signup action.
    """
    redirect_to = request.POST.get(redirect_field_name,
                                   request.GET.get(redirect_field_name, ''))

    if request.method == "POST":
        form = user_creation_form(request.POST)
        if form.is_valid():

            # Ensure the user-originating redirection url is safe.
            if not is_safe_url(url=redirect_to, host=request.get_host()):
                redirect_to = resolve_url(settings.LOGIN_REDIRECT_URL)

            # Okay, security check complete. Log the user in.
            user = form.save()
            _create_user_profile(request, user)
            user = authenticate(username=form.cleaned_data["username"], password=form.cleaned_data["password1"])
            auth_login(request, user)

            return HttpResponseRedirect(redirect_to)
    else:
        form = user_creation_form()

    current_site = get_current_site(request)

    context = {
        'form': form,
        redirect_field_name: redirect_to,
        'site': current_site,
        'site_name': current_site.name,
    }
    if extra_context is not None:
        context.update(extra_context)

    if current_app is not None:
        request.current_app = current_app

    return TemplateResponse(request, template_name, context)


class ProfileView(TemplateView):
    template_name = "accounts/profile.html"


class LoginRedirect(RedirectView):
    pattern = "login"


class IndexView(TemplateView):
    template_name = "index.html"


empty_map = {
    "2x1" : 18,
    "2x2" : 324,
    "3x1" : 81,
    "3x2" : 4374,
    "3x3" : 177147,
    "4x1" : 324,
    "4x2" : 52488,
    "4x3" : 6377292,
    "4x4" : 688747536,
    "5x1" : 1215,
    "5x2" : 590490,
    "5x3" : 215233605,
    "6x1" : 4374,
    "6x2" : 6377292,
    "7x1" : 15309,
    "7x2" : 66961566,
    "plus" : 6377292,
    "petal" : 20726199,
    "hassock" : 66961566,
    "twist" : 66961566,
    "notch" : 215233605,
}


class GoIndexView(TemplateView):
    template_name = "go_index.html"

    def get_context_data(self, *args, **kwargs):
        context = super(GoIndexView, self).get_context_data(*args, **kwargs)
        context["endgame_types"] = sorted(empty_map.keys())
        return context


class GoEmptyView(RedirectView):
    permanent = False
    pattern_name = "go"
    query_string = True
    def get_redirect_url(self, *args, **kwargs):
        endgame_type = kwargs["endgame_type"]
        if endgame_type not in empty_map:
            raise Http404

        endgame = empty_map[endgame_type]
        kwargs["endgame"] = str_base(endgame, 36)

        return super(GoEmptyView, self).get_redirect_url(*args, **kwargs)


class GoView(TemplateView):
    template_name = "go.html"

    def get_context_data(self, *args, **kwargs):
        context = super(GoView, self).get_context_data(*args, **kwargs)
        if kwargs["endgame_type"] not in empty_map:
            raise Http404
        context["endgame"] = int(context["endgame"], 36)
        context["mode"] = self.request.GET.get("mode", "normal")
        return context


class GoJSONView(View):
    def dispatch(self, *args, **kwargs):
        result = subprocess.check_output([settings.TABLE_QUERY_PATH, "go", kwargs["endgame_type"], kwargs["endgame"]])
        return HttpResponse(result)


class ChessIndexView(TemplateView):
    template_name = "chess_index.html"

    def get_context_data(self, *args, **kwargs):
        context = super(ChessIndexView, self).get_context_data(*args, **kwargs)
        context["low_endgames"] = low_endgames
        context["high_endgames"] = high_endgames
        return context


class ChessEditView(TemplateView):
    template_name = "chess_edit.html"


class ChessView(TemplateView):
    template_name = "chess.html"

    def get_context_data(self, *args, **kwargs):
        context = super(ChessView, self).get_context_data(*args, **kwargs)
        fen_parts = context["fen"].split("_")
        if len(fen_parts) < 2:
            fen_parts += "w"
        if len(fen_parts) < 3:
            fen_parts += "-"
        if len(fen_parts) < 4:
            fen_parts += "-"
        if len(fen_parts) < 5:
            fen_parts += "0"
        if len(fen_parts) < 6:
            fen_parts += "1"
        context["fen"] = " ".join(fen_parts)
        context["mode"] = self.request.GET.get("mode", "normal")
        return context


class ChessJSONView(View):
    def dispatch(self, *args, **kwargs):
        fen = kwargs["fen"].replace("_", " ")
        result = subprocess.check_output([settings.TABLE_QUERY_PATH, "chess", fen])
        return HttpResponse(result)


class Go9x9FAQView(TemplateView):
    template_name = "go9x9_faq.html"


class Go9x9View(TemplateView):
    template_name = "go9x9.html"
    def get_context_data(self, *args, **kwargs):
        context = super(Go9x9View, self).get_context_data(*args, **kwargs)
        if BOARD_SIZE == 9:
            context.setdefault("code", "h1000000000000000000000")
        else:
            raise NotImplementedError("Board size not supported")
        path_id = self.request.GET.get("path_id")
        if path_id is not None:
            path = Path.objects.get(pk=path_id)
            check_history_sanity([path.code] + path.undos + path.redos)
            context["path"] = True
            context["code"] = path.code
            context["undos"] = mark_safe(json.dumps(path.undos))
            context["redos"] = mark_safe(json.dumps(path.redos))
        game_id = self.request.GET.get("game_id")
        if game_id is not None:
            context["game_id"] = game_id
        return context

    @method_decorator(ensure_csrf_cookie)
    def dispatch(self, *args, **kwargs):
        return super(Go9x9View, self).dispatch(*args, **kwargs)


def get_user_activity_kwargs(request):
    if request.user.is_anonymous():
        return {"ip_address": get_ip(request)}
    else:
        return {"user": request.user}


LABELS = list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")
LABELS += [str(i) for i in range(1, 1 + BOARD_SIZE ** 2 - len(LABELS))] + ["pass"]


class Go9x9JSONView(View):
    def get(self, request, *args, **kwargs):
        user_kwargs = get_user_activity_kwargs(request)
        black_to_play = self.request.GET.get("player") != "white"
        sort = self.request.GET.get("sort")
        game_id = self.request.GET.get("game_id")
        code = kwargs["code"]
        board = code_to_board(code)
        result = board.to_json()
        result["endgame"] = code
        unique_children, redundant_children = board.children()
        moves = {}
        moves_by_code = {}
        redundant_moves_by_code = {}
        for move, child in unique_children:
            child_code = board_to_code(child)
            moves[move] = {"endgame": child_code}
            moves_by_code[child_code] = move
        for move, child in redundant_children:
            child_code = board_to_code(child)
            moves[move] = {"endgame": child_code}
            redundant_moves_by_code[child_code] = move

        state = State.objects.filter(code=code).select_related('position').first()
        if state:
            position = state.position
            result.update(position.to_json(state, black_to_play, **user_kwargs))
            total_continuations = 0
            qs = position.transitions.all().order_by('-times_played').prefetch_related('target__states')
            for transition in qs:
                total_continuations += transition.times_played
            if not total_continuations:
                total_continuations = 1  # Let's not divide by zero
            info = get_game_info(position, board=board, sort=sort, game_id=game_id, valid_codes=set(moves_by_code.keys()))
            if info is not None:
                result["info"] = info
            label_index = 0
            for transition in qs:
                target = transition.target
                for child_state in target.states.all():
                    if child_state.code in moves_by_code:
                        move = moves_by_code[child_state.code]
                        transition_info = transition.to_json(total_continuations, user_kwargs)
                        # target.bins skipped to save bandwidth
                        # transition_info["heuristic_value"] = target.heuristic_value  # Not implemented yet
                        transition_info["low_score"] = target.low_score
                        transition_info["high_score"] = target.high_score
                        # Player and opponent intentionally swapped because we're talking about a transition to the target.
                        transition_info["player_wins"] = target.opponent_wins
                        transition_info["opponent_wins"] = target.player_wins
                        transition_info["draws"] = target.draws
                        if transition.times_played or target.low_score is not None or target.position_infos.all().exists():
                            if move == "pass":
                                transition_info["label"] = "pass"
                            else:
                                transition_info["label"] = LABELS[label_index]
                                label_index += 1
                        moves[move].update(transition_info)
                    elif "heuristics" is "implemented" and child_state.code in redundant_moves_by_code:
                        move = redundant_moves_by_code[child_state.code]
                        moves[move]["heuristic_value"] = target.heuristic_value

        ms = []
        for coord, move_data in moves.items():
            move_data["coord"] = coord
            ms.append(move_data)
        ms.sort(key=lambda x: LABELS.index(x.get("label", LABELS[-2])))  # primary sort
        result["moves"] = ms
        result["status"] = "OK"
        return HttpResponse(json.dumps(result))

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        if "resolve" in data:
            result = self.resolve_position(data["resolve"])
            return HttpResponse(json.dumps(result))
        elif "message" in data:
            result = self.add_position_message(request, data)
            return HttpResponse(json.dumps(result))
        elif "message_action" in data:
            result = self.handle_message_action(request, data)
            return HttpResponse(json.dumps(result))
        elif "game_id" in data:
            result = self.vote_game(request, data)
            return HttpResponse(json.dumps(result))
        elif "path" in data:
            result = self.create_path(request, data)
            return HttpResponse(json.dumps(result))
        else:
            result = self.vote_transition(request, data)
            return HttpResponse(json.dumps(result))

    def vote_transition(self, request, data):
        transition_sanity_check(data["source"], data["target"])
        source, created = get_or_create_position(data["source"])
        target, created = get_or_create_position(data["target"])
        type_ = data["type"]
        transition, created = Transition.objects.get_or_create(source=source, target=target)
        user_kwargs = get_user_activity_kwargs(request)
        vote, created = TransitionVote.objects.get_or_create(transition=transition, **user_kwargs)
        vote.type = type_
        vote.save()
        transition.save()
        return transition.to_json()

    def vote_game(self, request, data):
        type_ = data["type"]
        game_info = GameInfo.objects.get(pk=int(data["game_id"]))
        user_kwargs = get_user_activity_kwargs(request)
        vote, created = GameVote.objects.get_or_create(game_info=game_info, **user_kwargs)
        vote.type = type_
        vote.save()
        game_info.cache_points()
        return game_info.points

    def resolve_position(self, history):
        source = None
        prev_code = None
        for code in history:
            position, created = get_or_create_position(code)
            if source:
                transition_sanity_check(prev_code, code)
                Transition.objects.get_or_create(source=source, target=position)
            source = position
            prev_code = code
        board = code_to_board(code)
        score = board.score()
        seen_pks = set()
        pre_cascade(position, seen_pks)
        position.low_score = score
        position.high_score = score
        position.save()
        for parent_transition in position.parent_transitions.all():
            cascade(parent_transition.source)
        return {
            "low_score": position.low_score,
            "high_score": position.high_score,
            "player_wins": position.player_wins,
            "opponent_wins": position.opponent_wins,
            "draws": position.draws,
        }

    def add_position_message(self, request, data):
        message = data["message"]
        black_to_play = data["black_to_play"]
        position, created = get_or_create_position(data["state"])
        state = position.states.filter(code=data["state"]).first()
        user_kwargs = get_user_activity_kwargs(request)
        message = PositionMessage.objects.create(position=position, state=state, black_to_play=black_to_play, content=message, **user_kwargs)
        return position.get_messages(state, black_to_play, **user_kwargs)

    def handle_message_action(self, request, data):
        user_kwargs = get_user_activity_kwargs(request)
        black_to_play = data["black_to_play"]
        state = State.objects.filter(code=data["state"]).first()
        action = data["message_action"]
        message = PositionMessage.objects.get(pk=data["pk"])
        if action == "flag":
            message.flags += 1
        elif action == "delete":
            message.deleted = True
        message.save()
        return state.position.get_messages(state, black_to_play, **user_kwargs)

    def create_path(self, request, data):
        # Sanity check in case someone is feeling scripty.
        code = data["state"]
        undos = data["undos"]
        redos = data["redos"]
        check_history_sanity([code] + undos + redos)
        path = Path.objects.create(code=code, undos=undos, redos=redos)
        return {
            "path_id": path.pk,
        }


def check_history_sanity(history):
    assert isinstance(history, list)
    for code in history:
        assert isinstance(code, basestring)
        assert len(code) == CODE_LENGTH
        assert all(c in chars64 for c in code)


def pre_cascade(position, seen_pks):
    """
    Pre-cascade to prevent infinite loops in the actual cascade.
    """
    if position.pk in seen_pks:
        return
    seen_pks.add(position.pk)
    # Constants chosen for debuging.
    position.low_score = -777
    position.high_score = 777
    position.save()
    for parent_transition in position.parent_transitions.all().select_related('source'):
        pre_cascade(parent_transition.source, seen_pks)


def cascade(position):
    """
    Negamax cascade

    The algorithm should converge, but as an added countermeasure
    we use the recursive approach to hit maximum recursion depth
    in case something goes wrong.
    """
    old_low = position.low_score
    old_high = position.high_score
    # Constants chosen for debuging.
    new_low = -888
    new_high = -888
    for transition in position.transitions.all().select_related('target'):
        child = transition.target
        if child.low_score is not None:
            new_high = max(new_high, -child.low_score)
        if child.high_score is not None:
            new_low = max(new_low, -child.high_score)
    if new_low == -888 or new_high == -888:
        raise ValueError("No child positions with score found.")
    if new_low != old_low or new_high != old_high:
        position.low_score = new_low
        position.high_score = new_high
        position.save()
        for parent_transition in position.parent_transitions.all().select_related('source'):
            cascade(parent_transition.source)


class Go9x9JSONEndView(View):
    """
    Get all states of the current game line to the end.
    """
    def get(self, request, *args, **kwargs):
        code = kwargs["code"]
        game_id = request.GET.get("game_id")
        if game_id is not None:
            game_id = int(game_id)
        result = []
        while True:
            board = code_to_board(code)
            state = State.objects.filter(code=code).first()
            if not state:
                break
            position = state.position
            if game_id is None:
                qs = position.transitions.filter(times_played__gt=0).order_by('-times_played').prefetch_related('target__states')
                if not qs.exists():
                    break
            else:
                game_info = GameInfo.objects.get(pk=game_id)
                position_info = position.position_infos.get(game_info=game_info)
                move_number = position_info.move_number
                next_info = game_info.position_infos.filter(move_number=(move_number + 1)).first()
                if next_info:
                    # Not really a queryset, but hey ducks.
                    qs = [Transition.objects.get(source=position, target=next_info.position)]
                else:
                    break
            valid_codes = set()
            for move, child in board.children(False):
                child_code = board_to_code(child)
                valid_codes.add(child_code)

            loop_detected = True
            for transition in qs:
                for child_state in transition.target.states.all():
                    if child_state.code in valid_codes:
                        code = child_state.code
                        if code not in result:
                            result.append(code)
                            loop_detected = False
                            break
                if not loop_detected:
                    break
            if loop_detected:
                break
        return HttpResponse(json.dumps(result));


def get_game_info(position=None, game_num=0, code=None, board=None, sort=None, game_id=None, valid_codes=None, user_kwargs=None):
    if not position:
        position = State.objects.filter(code=code).first().position
    # Secondary sort by date for unique order.
    position_infos = position.position_infos.all()
    if not position_infos.exists():
        return None
    if sort == "popularity":
        position_infos = position_infos.order_by("-game_info__points", "-game_info__created")
    elif sort == "date":
        position_infos = position_infos.order_by("-game_info__created")
    elif sort == "tree":
        position_infos = list(position_infos)
        position_infos.sort(key=lambda pi: pi.game_info.position_infos.all().order_by('-move_number').first().position.low_score is not None)
    else:
        position_infos = position_infos.order_by("-game_info__quality", "-game_info__created")
    if game_id is not None:
        game_id = int(game_id)
        if isinstance(position_infos, list):
            ids = [pi.game_info_id for pi in position_infos]
        else:
            ids = list(position_infos.values_list("game_info_id", flat=True))
        game_num = ids.index(game_id)
    position_info = position_infos[game_num]
    game_info = position_info.game_info
    if game_id is not None:
        assert game_info.pk == game_id
    info = game_info.to_json()
    move_number = position_info.move_number
    info["move_number"] = position_info.move_number
    info["total_games"] = len(position_infos)
    info["game_num"] = game_num
    next_info = game_info.position_infos.filter(move_number=(move_number + 1)).select_related('position').first()
    if next_info:
        target = next_info.position
        transition = Transition.objects.filter(source=position, target=target).prefetch_related('target__states').first()
        next_info = transition.to_json(user_kwargs=user_kwargs)
        if valid_codes is None:
            board = code_to_board(code)
            unique_children, _ = board.children()
            valid_codes = set(board_to_code(child) for coord, child in unique_children)
        for state in target.states.all():
            if state.code in valid_codes:
                next_info["endgame"] = state.code
                info["next"] = next_info
    previous_info = game_info.position_infos.filter(move_number=(move_number - 1)).prefetch_related('position__states').first()
    if previous_info:
        if board is None:
            board = code_to_board(code)
        source = previous_info.position
        for state in source.states.all():
            parent = code_to_board(state.code)
            for coord, child in parent.children(False):
                child.black_to_play = True
                if child == board:
                    info["previous"] = {"endgame": state.code}
                    break
            if "previous" in info:
                break
    return info


class Go9x9JSONGameView(View):
    def get(self, request, *args, **kwargs):
        code = kwargs["code"]
        game_num = int(kwargs["game_num"])
        sort = request.GET.get("sort")
        game_id = request.GET.get("game_id")
        user_kwargs = get_user_activity_kwargs(request)
        info = get_game_info(
            game_num=game_num,
            code=code,
            sort=sort,
            game_id=game_id,
            user_kwargs=user_kwargs,
        )
        return HttpResponse(json.dumps(info))



@csrf_exempt
@require_http_methods(["POST"])
def go9x9_add_sgf(request):
    data = json.loads(request.body)
    if data["password"] != settings.API_PASSWORD:
        raise ValueError("Too much hacking")
    process_sgf(data["sgf"], data.get("serious", True))
    return HttpResponse("OK")


@csrf_exempt
@require_http_methods(["POST"])
def go9x9_add_bins(request):
    data = json.loads(request.body)
    if data["password"] != settings.API_PASSWORD:
        raise ValueError("Maybe we should sign the requests instead")
    code = board_to_code(Board.from_json(data))
    position, created = get_or_create_position(code)
    position.add_bins(data["bins"])
    position.save()
