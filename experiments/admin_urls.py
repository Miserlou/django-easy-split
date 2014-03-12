# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from django.contrib.admin.views.decorators import staff_member_required

from django_lean.experiments.views import experiment_details, list_experiments


urlpatterns = patterns('django_lean.experiments.views',
    url(r'^(?P<experiment_name>.+)/$', staff_member_required(experiment_details), name="experiments_experiment_details"),
    url(r'^$', staff_member_required(list_experiments), name="experiments_list_experiments")
)
