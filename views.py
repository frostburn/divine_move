import json
import os
import subprocess

from django.conf import settings
from django.http import HttpResponse, Http404
from django.shortcuts import redirect
from django.views.generic import View, RedirectView, TemplateView

from utils import str_base
from chess_data import low_endgames, high_endgames


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
