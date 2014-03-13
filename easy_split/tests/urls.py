# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *


urlpatterns = patterns('easy_split.experiments.tests.views',
    url(r'^test-experiment/(?P<experiment_name>.*)$', 'experiment_test'),
    url(r'^test-clientsideexperiment/(?P<experiment_name>.*)$', 'clientsideexperiment_test')
)

urlpatterns += patterns('',
    url(r'^admin/', include('easy_split.experiments.admin_urls')),
    url(r'^main-app/', include('easy_split.experiments.urls')),
)

handler404 = 'easy_split.experiments.tests.views.dummy404'
