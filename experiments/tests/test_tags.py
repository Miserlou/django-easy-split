# -*- coding: utf-8 -*-
import mox

from django.core.urlresolvers import reverse
from django.template import Context
from django.test.client import Client
from django.contrib.auth.models import User

from django_lean.experiments.models import Experiment, Participant
from django_lean.experiments.templatetags.experiments import (
    experiment, clientsideexperiment
)
from django_lean.experiments.tests.utils import TestCase, TestUser


class ExperimentTagsTest(TestCase):
    urls = 'django_lean.experiments.tests.urls'
    
    def setUp(self):
        self.experiment = Experiment(name="test_experiment")
        self.experiment.save()
        self.experiment.state = Experiment.ENABLED_STATE
        self.experiment.save()
        
        self.other_experiment = Experiment(name="other_test_experiment")
        self.other_experiment.save()
        self.other_experiment.state = Experiment.ENABLED_STATE
        self.other_experiment.save()
        self.mox = mox.Mox()
    
    def testIntegrationWithAnonymousVisitor(self):
        self.doTestIntegration(
            url=reverse('django_lean.experiments.tests.views.experiment_test',
                        args=[self.experiment.name]),
            client_factory=lambda i: Client())
        self.doTestIntegration(
            url=reverse('django_lean.experiments.tests.views.clientsideexperiment_test',
                        args=[self.other_experiment.name]),
            client_factory=lambda i: Client())
    
    def testIntegrationWithRegisteredUser(self):
        def create_registered_user_client(i):
            user = User(username="user%s" % i, email="user%s@example.com" % i)
            user.set_password("password")
            user.save()
            
            client = Client()
            
            if not client.login(username=user.username, password="password"):
                raise Exception("login failure")
            return client
        self.doTestIntegration(
            url=reverse('django_lean.experiments.tests.views.experiment_test',
                        args=[self.experiment.name]),
            client_factory=create_registered_user_client)
        
        # we wrap our factory to ensure that the users are created
        # with new names
        self.doTestIntegration(
            url=reverse('django_lean.experiments.tests.views.clientsideexperiment_test',
                        args=[self.other_experiment.name]),
            client_factory=lambda i: create_registered_user_client(1000 + i))
    
    def doTestIntegration(self, url, client_factory):
        confirm_human_url = reverse('django_lean.experiments.views.confirm_human')
        found_control = False
        found_test = False
        for i in range(100):
            client = client_factory(i)
            response = client.get(confirm_human_url)
            self.assertEquals(204, response.status_code)
            response = client.get(url)
            self.assertEquals(200, response.status_code)
            in_test = "test" in response.content.lower()
            in_control = "control" in response.content.lower()
            self.assertTrue(in_test != in_control)
            found_control = found_control or in_control
            found_test = found_test or in_test
        
        self.assertTrue(found_control)
        self.assertTrue(found_test)
    
    def testIllegalGroupName(self):
        self.doRenderExperiment("username", "foo group",
                                expect_render_exception=True)
    
    def testBadSyntax(self):
        self.doRenderExperimentToken(
            "username", ("experiment", self.experiment.name, "group", "yeah"),
            expect_parse_exception=True)
    
    def doRenderExperimentToken(self, username, token_tuple,
                           expect_parse_exception=False,
                           expect_render_exception=False):
        internal_render_result = "rendered"
        parser = self.mox.CreateMockAnything()
        child_node_list = self.mox.CreateMockAnything()
        context = {}
        user_factory = self.mox.CreateMockAnything()
        token = self.mox.CreateMockAnything()
        token.split_contents().AndReturn(token_tuple)
        parser.parse(('endexperiment', )).MultipleTimes().AndReturn(
            child_node_list)
        parser.delete_first_token().MultipleTimes()
        user_factory.create_user(context).MultipleTimes().AndReturn(
            TestUser(username=username))
        child_node_list.render(context).MultipleTimes().AndReturn(
            internal_render_result)
        
        self.mox.ReplayAll()
        
        # HACK: there is no way to make a call optional
        child_node_list.render(context)
        parser.parse(('endexperiment', ))
        parser.delete_first_token()
        user_factory.create_user(context)

        
        do_parse = lambda: experiment(parser, token, user_factory=user_factory)
        if expect_parse_exception:
            self.assertRaises(Exception, do_parse)
        else:
            node = do_parse()
        
        if expect_parse_exception:
            self.mox.VerifyAll()
            return None
        
        do_render = lambda: node.render(context)
        if expect_render_exception:
            self.assertRaises(Exception, do_render)
        else:
            actual_render_result = do_render()
        
        if expect_render_exception:
            self.mox.VerifyAll()
            return None
        
        self.mox.VerifyAll()
        
        self.assertTrue(actual_render_result == "" or
                        actual_render_result == internal_render_result)
        in_group = (actual_render_result == internal_render_result)
        return in_group
    
    def doRenderExperiment(self, username, groupname, **kwargs):
        return self.doRenderExperimentToken(
            username, ("experiment", self.experiment.name, groupname),
            **kwargs)
    
    def testExperimentTag(self):
        found_test = False
        found_control = False
        
        for i in range(100):
            username = "user%s" % i
            in_test = self.doRenderExperiment(username, "test")
            found_test = found_test or in_test
            found_control = found_control or (not in_test)
            
            # make sure we get the same result from a second call
            self.assertEquals(in_test,
                              self.doRenderExperiment(username, "test"))
            
            # make sure that the result of calling control is the opposite of
            # the result of calling test
            in_control = self.doRenderExperiment(username, "control")
            self.assertEquals(not in_test, in_control)
        
        self.assertTrue(found_control and found_test)
    
    def doRenderClientSideExperiment(self, context, username, experiment_name):
        parser = self.mox.CreateMockAnything()
        user_factory = self.mox.CreateMockAnything()
        token = self.mox.CreateMockAnything()
        token.split_contents().AndReturn(("clientsideexperiment",
                                          experiment_name))
        user_factory.create_user(context).MultipleTimes().AndReturn(
            TestUser(username=username))
        
        self.mox.ReplayAll()
        
        # HACK this is the only way to make a call optional
        user_factory.create_user(context)
        
        node = clientsideexperiment(parser, token, user_factory=user_factory)
        node.render(context)
        
        self.mox.VerifyAll()
    
    def testClientSideExperimentTag(self):
        for i in range(100):
            user = User(username="user%s" % i, email="user%s@example.com" % i)
            user.save()
            
            # create a context for a single "request"
            c = Context({"user": user})
            
            self.doRenderClientSideExperiment(c, "user%i" % i,
                                              self.experiment.name)
            self.assertTrue("client_side_experiments" in c)
            self.doRenderClientSideExperiment(c, "user%i" % i,
                                              self.experiment.name)
            self.doRenderClientSideExperiment(c, "user%i" % i,
                                              self.other_experiment.name)
            self.doRenderClientSideExperiment(c, "user%i" % i,
                                              self.other_experiment.name)
            
            # determine what group the user was assigned to in each experiment
            experiment_partcipant = Participant.objects.get(
                                        user=user,
                                        experiment=self.experiment)
            other_experiment_partcipant = Participant.objects.get(
                                            user=user,
                                            experiment=self.other_experiment)
            
            # assert that exactly two entries were populated in the
            # 'client_side_experiments' dict in the context and that they are
            # equal to the names of our two experiments
            self.assertEquals(2, len(c['client_side_experiments'].keys()))
            self.assertTrue(self.experiment.name in
                               c['client_side_experiments'])
            self.assertTrue(self.other_experiment.name in
                               c['client_side_experiments'])
            
            # get the values that were put in the client_side_experiments dict
            group_name = c['client_side_experiments'][self.experiment.name]
            other_group_name = \
                c['client_side_experiments'][self.other_experiment.name]
            
            # make sure that the values correctly represent the user's
            # enrollments
            group_id = experiment_partcipant.group
            other_group_id = other_experiment_partcipant.group
            self.assertEqual(group_id == Participant.TEST_GROUP,
                             group_name == "test")
            
            self.assertEqual(group_id == Participant.CONTROL_GROUP,
                             group_name == "control")
            
            self.assertEqual(
                        other_group_id == Participant.TEST_GROUP,
                        other_group_name == "test")
            
            self.assertEqual(
                        other_group_id == Participant.CONTROL_GROUP,
                        other_group_name == "control")
    
