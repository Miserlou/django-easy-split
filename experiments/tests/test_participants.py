# -*- coding: utf-8 -*-
from django.conf import settings

from django_lean.experiments.models import Experiment
from django_lean.experiments.tests.utils import TestCase, TestUser


class TestParticipants(TestCase):
    def testDisabledExperiment(self):
        # disabled test (unenrolled user)
        experiment = Experiment(name="disabled")
        experiment.save()
        user = TestUser(username="user1")
        self.assertFalse(Experiment.test("disabled", user))
        self.assertTrue(Experiment.control("disabled", user))

    def testUnknownExperiment(self):
        # unknown test (unenrolled user)
        user = TestUser(username="user1")
        
        # unit tests are always run in DEBUG=False by Django
        self.assertFalse(Experiment.test("undefined", user))
        self.assertTrue(Experiment.control("undefined", user))

        try:
            settings.DEBUG = True
            self.assertRaises(Exception,
                              lambda: Experiment.test("undefined", user))
            self.assertRaises(Exception,
                              lambda: Experiment.control("undefined", user))
        finally:
            settings.DEBUG = False

    def testPromotedExperiment(self):
        # promoted test (unenrolled user)
        experiment = Experiment(name="promoted")
        experiment.save()
        experiment.state = Experiment.PROMOTED_STATE
        experiment.save()
        user = TestUser(username="user1")
        self.assertTrue(Experiment.test("promoted", user))
        self.assertFalse(Experiment.control("promoted", user))

    def testAnonymousUser(self):
        experiment = Experiment(name="enabled")
        experiment.save()
        experiment.state = Experiment.ENABLED_STATE
        experiment.save()
        for i in range(100):
            user = TestUser()
            in_test = Experiment.test("enabled", user)
            anonymous_id = user.get_anonymous_id()
            self.assertNotEquals(None, anonymous_id)
            in_control = Experiment.control("enabled", user)
            self.assertEquals(user.get_anonymous_id(), anonymous_id)
            self.assertNotEquals(in_test, in_control)
            self.assertEquals(in_test, Experiment.test("enabled", user))
            self.assertEquals(user.get_anonymous_id(), anonymous_id)
            self.assertEquals(in_control, Experiment.control("enabled", user))
            self.assertEquals(user.get_anonymous_id(), anonymous_id)

            if in_test:
                test_user = user
            if in_control:
                control_user = user

        self.assertTrue(test_user and control_user)

        user = TestUser()
        experiment = Experiment(name="disabled")
        experiment.save()
        self.assertFalse(Experiment.test("disabled", user))
        self.assertEquals(None, user.get_anonymous_id())

    def testEnabledPromotedAndDisabledExperiment(self):
        # enabled test, new user (prove we get both results)
        experiment = Experiment(name="enabled")
        experiment.save()
        experiment.state = Experiment.ENABLED_STATE
        experiment.save()
        test_user = None
        control_user = None
        for i in range(100):
            user = TestUser(username="user%s" % i)
            in_test = Experiment.test("enabled", user)
            in_control = Experiment.control("enabled", user)
            self.assertNotEquals(in_test, in_control)
            self.assertEquals(in_test, Experiment.test("enabled", user))
            self.assertEquals(in_control, Experiment.control("enabled", user))
            if in_test:
                test_user = user
            if in_control:
                control_user = user

        self.assertNotEquals(None, test_user)
        self.assertNotEquals(None, control_user)
        self.assertNotEquals(test_user, control_user)

        # promoted test with an enrolled user
        # (prove we get both results, then that all users are in test)
        experiment.state = Experiment.PROMOTED_STATE
        experiment.save()

        self.assertFalse(Experiment.control("enabled", control_user))
        self.assertFalse(Experiment.control("enabled", test_user))
        self.assertTrue(Experiment.test("enabled", control_user))
        self.assertTrue(Experiment.test("enabled", test_user))

        # disabled test with an enrolled user
        # (prove we get both results, then that all users are in control)
        experiment.state = Experiment.DISABLED_STATE
        experiment.save()

        self.assertTrue(Experiment.control("enabled", control_user))
        self.assertTrue(Experiment.control("enabled", test_user))
        self.assertFalse(Experiment.test("enabled", control_user))
        self.assertFalse(Experiment.test("enabled", test_user))
    
