import json
import os
import subprocess

from django.conf import settings
from django.http import HttpResponse, Http404
from django.shortcuts import redirect
from django.views.generic import View, TemplateView

from utils import str_base

class IndexView(TemplateView):
    template_name = "index.html"

empty_map = {
    "4x3": 6377292,
    "5x3": 215233605,
    "4x4": 688747536,
}

class GoEmptyView(View):
    def get(self, *args, **kwargs):
        endgame_type = kwargs["endgame_type"]
        if endgame_type not in empty_map:
            raise Http404

        endgame = empty_map[endgame_type]

        return redirect("go", endgame_type, str_base(endgame, 36))

class GoView(TemplateView):
    template_name = "go.html"

    def get_context_data(self, *args, **kwargs):
        context = super(GoView, self).get_context_data(*args, **kwargs)
        if kwargs["endgame_type"] not in empty_map:
            raise Http404
        context["endgame"] = int(context["endgame"], 36)
        return context

class GoJSONView(View):
    def dispatch(self, *args, **kwargs):
        result = subprocess.check_output([settings.TABLE_QUERY_PATH, "go", kwargs["endgame_type"], kwargs["endgame"]])
        return HttpResponse(result)
