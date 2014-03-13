# -*- coding: utf-8 -*-
import logging
l = logging.getLogger(__name__)

from django.template import Template, RequestContext
from django.http import HttpResponse
from django.views.decorators.cache import never_cache


EXPERIMENT_TEMPLATE = """
{%% load experiments %%}
{%% experiment %(experiment_name)s test %%}TEST{%% endexperiment %%}
{%% experiment %(experiment_name)s control %%}CONTROL{%% endexperiment %%}
"""

CLIENTSIDEEXPERIMENT_TEMPLATE = """
{%% load experiments %%}
{%% clientsideexperiment %(experiment_name)s %%}
{{ client_side_experiments.%(experiment_name)s }}
"""

@never_cache
def experiment_test(request, experiment_name):
    t = Template(EXPERIMENT_TEMPLATE % {'experiment_name': experiment_name} )
    return HttpResponse(t.render(RequestContext(request)))

@never_cache
def clientsideexperiment_test(request, experiment_name):
    t = Template(CLIENTSIDEEXPERIMENT_TEMPLATE % {'experiment_name': experiment_name} )
    return HttpResponse(t.render(RequestContext(request)))

def dummy404(request):
    return HttpResponse(status=404, content="Not found", content_type="text/plain")
