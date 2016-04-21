# -*- coding: utf-8 -*-
from django.conf import settings

def external_links(request):
    links = getattr(settings, "EXTERNAL_LINKS", [])
    return {"external_links": links}
