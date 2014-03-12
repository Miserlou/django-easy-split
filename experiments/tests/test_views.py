# -*- coding: utf-8 -*-
from BeautifulSoup import BeautifulSoup
from datetime import date, timedelta

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test.client import Client

from django_lean.experiments.models import (Experiment, Participant,
                                            DailyEngagementReport,
                                            AnonymousVisitor,
                                            GoalType, DailyConversionReport,
                                            DailyConversionReportGoalData)
from django_lean.experiments.tests.utils import TestCase


def get_tables(html):
    results = []
    soup = BeautifulSoup(html)
    for table in soup.findAll('table'):
        rows = table.findAll('tr')
        # Extract the header row
        header = rows.pop(0).findAll('th', text=True)
        header = [h.strip() for h in header if h.strip()]
        # Clean up the data in the table
        data = [r.findAll('td', text=True) for r in rows]
        for row in data:
            row[:] = [d.strip() for d in row if d.strip()]
        results.append((header, data))
    return results

def days_ago(days):
    return date.today() - timedelta(days=days)

class TestExperimentViews(object):
    urls = 'experiments.tests.urls'
    
    def setUp(self):
        staff_user = User(username="staff_user", email="staff@example.com",
                          is_staff=True)
        staff_user.save()
        staff_user.set_password("staff")
        staff_user.save()
        
        # self.assertTrue(self.client.login(username='staff_user',
        #                                   password='staff'))
        
        self.experiment1 = Experiment(name="experiment 1")
        self.experiment1.save()
        self.experiment1.state = Experiment.ENABLED_STATE
        self.experiment1.save()
        self.experiment1.start_date -= timedelta(days=5)
        self.experiment1.save()
        
        goal_types = [GoalType.objects.create(name='test_goal_%s' % i)
                      for i in range(3)]
        
        for i in range(1, 6):
            DailyEngagementReport.objects.create(date=days_ago(i),
                                                 experiment=self.experiment1,
                                                 control_score=3.2,
                                                 test_score=2.3,
                                                 control_group_size=3,
                                                 test_group_size=5,
                                                 confidence=93.2)
            conversion_report = DailyConversionReport.objects.create(
                date=days_ago(i),
                experiment=self.experiment1,
                overall_test_conversion=12,
                overall_control_conversion=9,
                test_group_size=39,
                control_group_size=27,
                confidence=87.4)
            for goal_type in goal_types:
                DailyConversionReportGoalData.objects.create(
                    report=conversion_report,
                    goal_type=goal_type,
                    test_conversion=11,
                    control_conversion=7,
                    confidence=45.3)
        
        self.experiment2 = Experiment(name="experiment 2")
        self.experiment2.save()
        
        self.experiment3 = Experiment(name="experiment 3")
        self.experiment3.save()
        self.experiment3.state = Experiment.ENABLED_STATE
        self.experiment3.save()
        self.experiment3.state = Experiment.PROMOTED_STATE
        self.experiment3.save()
    
    def testListExperimentsView(self):
        url = reverse('experiments.views.list_experiments')
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        header, data = get_tables(response.content)[0]
        data.sort()
        self.assertEquals([u'Name', u'Status', u'Start Date', u'End Date'],
                          header)
        self.assertEquals([[u'experiment 1', u'Enabled',
                            unicode(self.experiment1.start_date), u'None'],
                           [u'experiment 2', u'Disabled', u'None', u'None'],
                           [u'experiment 3', u'Promoted',
                            unicode(self.experiment3.start_date),
                            unicode(self.experiment3.end_date)]],
                          data)
    
    def testAnonymousUserCannotAccessReports(self):
        self.client.logout()
        url = reverse('experiments.views.experiment_details',
                      args=['experiment 1'])
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        self.assertTrue('<title>Log in' in response.content)
        url = reverse('experiments.views.list_experiments')
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        self.assertTrue('<title>Log in' in response.content)
    
    def testRegularUserCannotAccessReports(self):
        self.client.logout()
        
        regular_user = User(username="regular_user", email="joe@example.com")
        regular_user.save()
        regular_user.set_password("joe")
        regular_user.save()
        
        self.assertTrue(self.client.login(username='regular_user',
                                          password='joe'))
        
        url = reverse('experiments.views.experiment_details',
                      args=['experiment 1'])
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        self.assertTrue('<title>Log in' in response.content)
        url = reverse('experiments.views.list_experiments')
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        self.assertTrue('<title>Log in' in response.content)
    
    def test404IfExperimentDoesntExist(self):
        url = reverse('experiments.views.experiment_details',
                      args=['inexistant experiment'])
        response = self.client.get(url)
        self.assertEquals(response.status_code, 404)
    
    def testExperimentDetailsView(self):
        url = reverse('experiments.views.experiment_details',
                      args=['experiment 1'])
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        tables = get_tables(response.content)
        experiment_properties = tables.pop(0)
        self.assertEquals([u'Property', u'Value'],
                          experiment_properties[0])
        self.assertEquals([[u'Experiment Name', u'experiment 1'],
                           [u'Status', u'Enabled'],
                           [u'Start Date',
                            unicode(self.experiment1.start_date)],
                           [u'End Date', u'None']],
                          experiment_properties[1])
        conversion_summary = tables.pop(0)
        self.assertEquals([u'&nbsp;', u'Control Group', u'Test Group',
                           u'Improvement', u'Confidence'],
                          conversion_summary[0])
        self.assertEquals([[u'Participants', u'27', u'39', u'&nbsp;',
                            u'&nbsp;'],
                           [u'test_goal_0', u'7 (25.9 %)', u'11 (28.2 %)',
                            u'8 %', u'45 %'],
                           [u'test_goal_1', u'7 (25.9 %)', u'11 (28.2 %)',
                            u'8 %', u'45 %'],
                           [u'test_goal_2', u'7 (25.9 %)', u'11 (28.2 %)',
                            u'8 %', u'45 %'],
                           [u'Any', u'9 (33.3 %)', u'12 (30.8 %)', u'-7 %',
                            u'87 %']],
                          conversion_summary[1])
        engagement_summary = tables.pop(0)
        self.assertEquals([u'&nbsp;', u'Control Group', u'Test Group',
                           u'Improvement', u'Confidence'],
                          engagement_summary[0])
        self.assertEquals([[u'Participants', u'3', u'5', u'&nbsp;', u'&nbsp;'],
                           [u'Engagement Score', u'3.2', u'2.3', u'-28 %',
                            u'93 %']],
                          engagement_summary[1])
        conversion_details = tables.pop(0)
        self.assertTrue(conversion_details[0])
        self.assertTrue(conversion_details[1])
        engagement_details = tables.pop(0)
        self.assertEquals([u'Report Date', u'Control Group Size',
                           u'Control Group Score', u'Test Group Size',
                           u'Test Group Score', u'Test Group Improvement',
                           u'Confidence'],
                          engagement_details[0])
        self.assertEquals([unicode(days_ago(1)), u'3', u'3.2', u'5', u'2.3',
                           u'-28 %', u'93 %'],
                          engagement_details[1][0])
        self.assertEquals([], tables)
    
    def testVerifyHuman(self):
        experiment = Experiment(name="experiment")
        experiment.save()
        experiment.state = Experiment.ENABLED_STATE
        experiment.save()
        
        other_experiment = Experiment(name="other_experiment")
        other_experiment.save()
        other_experiment.state = Experiment.ENABLED_STATE
        other_experiment.save()
        
        self.client = Client()
        
        original_participants_count = Participant.objects.all().count()
        original_anonymous_visitors_count = AnonymousVisitor.objects.all().count()
        experiment_url = reverse('experiments.tests.views.experiment_test',
                                 args=[experiment.name])
        response = self.client.get(experiment_url)
        self.assertEquals(response.status_code, 200)
        
        self.assertEquals(original_participants_count,
                          Participant.objects.all().count())
        self.assertEquals(original_anonymous_visitors_count,
                          AnonymousVisitor.objects.all().count())
        
        confirm_human_url = reverse('experiments.views.confirm_human')
        response = self.client.get(confirm_human_url)
        self.assertEquals(response.status_code, 204)
        self.assertEquals(0, len(response.content))
        self.assertEquals(original_participants_count+1,
                          Participant.objects.all().count())
        self.assertEquals(original_anonymous_visitors_count+1,
                          AnonymousVisitor.objects.all().count())
        
        # calling it again does nothing
        response = self.client.get(confirm_human_url)
        self.assertEquals(response.status_code, 204)
        self.assertEquals(0, len(response.content))
        self.assertEquals(original_participants_count+1,
                          Participant.objects.all().count())
        self.assertEquals(original_anonymous_visitors_count+1,
                          AnonymousVisitor.objects.all().count())
        
        other_experiment_url = reverse(
            'experiments.tests.views.experiment_test',
            args=[other_experiment.name])
        response = self.client.get(other_experiment_url)
        self.assertEquals(response.status_code, 200)
        
        # a new participant is immediately created for the new experiment
        self.assertEquals(original_participants_count + 2,
                          Participant.objects.all().count())
        # the existing anonymous visitor is reused
        self.assertEquals(original_anonymous_visitors_count + 1,
                          AnonymousVisitor.objects.all().count())
        
        # the new experiment does not cause storage of a temporary enrollment
        response = self.client.get(confirm_human_url)
        self.assertEquals(response.status_code, 204)
        self.assertEquals(0, len(response.content))
        self.assertEquals(original_participants_count+2,
                          Participant.objects.all().count())
        self.assertEquals(original_anonymous_visitors_count+1,
                          AnonymousVisitor.objects.all().count())
    
    def testGroupSanity(self):
        experiment = Experiment(name="experiment")
        experiment.save()
        experiment.state = Experiment.ENABLED_STATE
        experiment.save()
        experiment_url = reverse('experiments.tests.views.experiment_test',
                                 args=[experiment.name])
        for i in range(100):
            self.client = Client()
            response = self.client.get(experiment_url)
            self.assertEquals(response.status_code, 200)
            self.assertTrue(response.content.strip().lower() in ("test",
                                                                 "control"))
