# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *


urlpatterns = patterns('django_lean.experiments.views',
    url(r'^goal/(?P<goal_name>.*)$', 'record_experiment_goal'),
    url(r'^confirm_human/$', 'confirm_human')
)
