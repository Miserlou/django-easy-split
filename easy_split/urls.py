# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'^goal/(?P<goal_name>.*)$', 'easy_split.views.record_experiment_goal'),
    url(r'^confirm_human/$', 'easy_split.views.confirm_human')
)
