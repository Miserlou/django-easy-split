# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test.client import Client

from django_lean.experiments.models import (AnonymousVisitor, Experiment,
                                            GoalRecord, GoalType)
from django_lean.experiments.tests.utils import TestCase
from django_lean.experiments.views import TRANSPARENT_1X1_PNG


class BugViewTest(TestCase):
    urls = 'django_lean.experiments.tests.urls'
    
    def call_goal(self, client, goal):
        url = reverse('django_lean.experiments.views.record_experiment_goal',
                      args=[goal])
        response = client.get(url)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response['Content-Type'], 'image/png')
        self.assertEquals(response['Cache-Control'], 'max-age=0')
        self.assertEquals(response.content, TRANSPARENT_1X1_PNG)

    def testPngResponse(self):
        experiment = Experiment(name="test-experiment")
        experiment.save()
        experiment.state = Experiment.ENABLED_STATE
        experiment.save()
        
        goal_type = GoalType(name='test-goal')
        goal_type.save()
        
        experiment_url = reverse("django_lean.experiments.tests.views.experiment_test",
                                 args=[experiment.name])
        confirm_human_url = reverse("django_lean.experiments.views.confirm_human")
        
        client = Client()
        
        # we can call with invalid or inexisting names, the response is the same
        self.call_goal(client, '')
        self.call_goal(client, 'unknown-goal')
        
        # this is an anonymous visitor not enrolled in an experiment,
        # so no records should be created
        self.call_goal(client, goal_type.name)
        
        self.assertEquals(0, GoalRecord.objects.filter(goal_type=goal_type).count())
        
        nb_anonymous_visitors = AnonymousVisitor.objects.count()
        # force the user to be a verified human
        response = client.get(confirm_human_url)
        self.assertEquals(response.status_code, 204)
        
        # force the anonymous visitor to be enrolled in an experiment
        response = client.get(experiment_url)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(nb_anonymous_visitors + 1,
                          AnonymousVisitor.objects.count())
        client.get('/test-experiment/%s' % experiment.name)
        self.assertEquals(nb_anonymous_visitors + 1,
                          AnonymousVisitor.objects.count())
        
        # now call an existing goal again - it should be recorded
        self.call_goal(client, goal_type.name)
        self.assertEquals(1, GoalRecord.objects.filter(goal_type=goal_type).count())
        
        # should be recorded again
        self.call_goal(client, goal_type.name)
        self.assertEquals(2, GoalRecord.objects.filter(goal_type=goal_type).count())
        
        # validate that both of the records have the same anonymous_visitor
        two_goal_records = GoalRecord.objects.filter(goal_type=goal_type)
        self.assertEquals(two_goal_records[0].anonymous_visitor,
                          two_goal_records[1].anonymous_visitor)
        
        # try it with a registered user
        client = Client()
        user = User(username="testuser", email="testuser@example.com")
        user.set_password("password")
        user.save()
        
        response = client.login(username=user.username, password='password')
        self.assertTrue(response)
        
        # force the registered user to be enrolled in an experiment
        client.get('/test-experiment/%s' % experiment.name)
        
        self.call_goal(client, goal_type.name)
        # since the user was registered, no new records should be created
        self.assertEquals(2, GoalRecord.objects.filter(goal_type=goal_type).count())
    
