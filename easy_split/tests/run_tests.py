# -*- coding: utf-8 -*-
from django.conf import settings


class SimpleEngagementCalculator(object):
    def calculate_user_engagement_score(self, user, start_date, end_date):
	    return 0

if __name__ == '__main__':
	settings.configure(
            ROOT_URLCONF=None,
            LEAN_ENGAGEMENT_CALCULATOR=(
                'experiments.tests.run_tests.SimpleEngagementCalculator'),
            DATABASE_ENGINE='sqlite3',
            DATABASE_NAME=':memory:',
            DATABASE_SUPPORTS_TRANSACTIONS=False,
            INSTALLED_APPS=[
                'django.contrib.auth',
                'django.contrib.contenttypes',
                'django.contrib.sessions',
                'django.contrib.sites',
                'experiments'],
            TEMPLATE_CONTEXT_PROCESSORS =(
                "django.core.context_processors.auth",
                "django.core.context_processors.debug",
                "django.core.context_processors.i18n",
                "django.core.context_processors.media",
                "django.core.context_processors.request")
            )
	from django.core.management import call_command
	call_command('syncdb', interactive=False)
	call_command('test', 'experiments')
