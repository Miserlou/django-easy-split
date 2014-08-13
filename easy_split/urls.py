# -*- coding: utf-8 -*-
try:
    from django.conf.udrls import patterns, include, url
except ImportError:
    from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('',
    url(r'^goal/(?P<goal_name>.*)$', 'easy_split.views.record_experiment_goal'),
    url(r'^confirm_human/$', 'easy_split.views.confirm_human')
)
