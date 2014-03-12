# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *


urlpatterns = patterns('django_lean.experiments.tests.views',
    url(r'^test-experiment/(?P<experiment_name>.*)$', 'experiment_test'),
    url(r'^test-clientsideexperiment/(?P<experiment_name>.*)$', 'clientsideexperiment_test')
)

urlpatterns += patterns('',
    url(r'^admin/', include('django_lean.experiments.admin_urls')),
    url(r'^main-app/', include('django_lean.experiments.urls')),
)

handler404 = 'django_lean.experiments.tests.views.dummy404'
