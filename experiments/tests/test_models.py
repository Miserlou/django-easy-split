# -*- coding: utf-8 -*-
from __future__ import with_statement
from datetime import datetime

from django.conf import settings
from django.contrib.auth.models import User

from django_lean.experiments.models import (Experiment, Participant,
                                            AnonymousVisitor,
                                            GoalType, GoalRecord)
from django_lean.experiments.tests.utils import TestCase, TestUser, patch


class TestExperimentModels(TestCase):
    def testExperimentStates(self):
        experiment1 = Experiment(name="test_experiment_1")
        experiment1.save()
        
        experiment1 = Experiment.objects.get(name="test_experiment_1")
        
        self.assertRaises(Exception,
                          lambda: Experiment(name="test_experiment_1").save())
        
        #test default values
        self.assertEquals(experiment1.state, Experiment.DISABLED_STATE)
        self.assertEquals(experiment1.start_date, None)
        self.assertEquals(experiment1.end_date, None)
        
        #enable the experiment
        experiment1.state = Experiment.ENABLED_STATE
        experiment1.save()
        
        self.assertNotEquals(experiment1.start_date, None)
        self.assertEquals(experiment1.end_date, None)
        
        #disable the experiement
        old_start_date = experiment1.start_date
        experiment1.state = Experiment.DISABLED_STATE
        experiment1.save()
        self.assertEquals(experiment1.start_date, old_start_date)
        self.assertNotEquals(experiment1.end_date, None)
        
        #enable the experiment
        old_end_date = experiment1.end_date
        experiment1.state = Experiment.ENABLED_STATE
        experiment1.save()
        
        self.assertEquals(experiment1.start_date, old_start_date)
        self.assertEquals(experiment1.end_date, old_end_date)
        
        #promote the experiment
        experiment1.state = Experiment.PROMOTED_STATE
        experiment1.save()
        
        self.assertEquals(experiment1.start_date, old_start_date)
        self.assertEquals(experiment1.end_date, old_end_date)
        
        experiment2 = Experiment(name= "Experiment 2")
        experiment2.save()
        experiment2.state = Experiment.ENABLED_STATE
        experiment2.save()
        self.assertEquals(experiment2.start_date, experiment1.start_date)
        experiment2.state = Experiment.PROMOTED_STATE
        experiment2.save()
        
        self.assertNotEquals(experiment2.start_date, None)
        self.assertNotEquals(experiment2.end_date, None)
    
    def testParticipants(self):
        user1 = User(username="user1", email="email1@example.com")
        user1.save()
        user2 = User(username="user2", email="email2@example.com")
        user2.save()
        user3 = User(username="user3", email="email3@example.com")
        user3.save()
        
        anonymous_visitor1 = AnonymousVisitor()
        anonymous_visitor1.save()
        anonymous_visitor2 = AnonymousVisitor()
        anonymous_visitor2.save()
        anonymous_visitor3 = AnonymousVisitor()
        anonymous_visitor3.save()
        
        experiment1 = Experiment(name="Experiment 1")
        experiment1.save()
        experiment2 = Experiment(name="Experiment 2")
        experiment2.save()
        
        participant11 = Participant(user=user1,
                                    experiment= experiment1,
                                    group=Participant.CONTROL_GROUP)
        participant11.save()
        participant12 = Participant(user=user1,
                                    experiment= experiment2,
                                    group=Participant.TEST_GROUP)
        participant12.save()
        participant21 = Participant(user=user2,
                                    experiment= experiment1,
                                    group=Participant.CONTROL_GROUP)
        participant21.save()
        participant22 = Participant(user=user2,
                                    experiment= experiment2,
                                    group=Participant.CONTROL_GROUP)
        participant22.save()
        
        self.assertRaises(Exception,
                          lambda: Participant(user=user2,
                                              experiment= experiment2,
                                              group=Participant.TEST_GROUP).save())
        
        # create anonymous participants
        participant31 = Participant(anonymous_visitor=anonymous_visitor1,
                                    experiment=experiment1,
                                    group=Participant.CONTROL_GROUP)
        participant31.save()
        participant32 = Participant(anonymous_visitor=anonymous_visitor1,
                                    experiment=experiment2,
                                    group=Participant.TEST_GROUP)
        participant32.save()
        participant42 = Participant(anonymous_visitor=anonymous_visitor2,
                                    experiment=experiment2,
                                    group=Participant.CONTROL_GROUP)
        participant42.save()
        
        self.assertRaises(Exception,
                          lambda: Participant(anonymous_visitor=anonymous_visitor1,
                                              experiment=experiment1,
                                              group=Participant.TEST_GROUP).save())
        
        self.assertRaises(Exception,
                          lambda: Participant(experiment=experiment1,
                                              group=Participant.TEST_GROUP).save())
        
        self.assertRaises(Exception,
                          lambda: Participant(user=user3,
                                              anonymous_visitor=anonymous_visitor3,
                                              experiment=experiment1,
                                              group=Participant.TEST_GROUP))
        self.assertRaises(Exception,
                          lambda: Participant(user=user3,
                                              experiment=experiment1).save())
        
        self.assertNotEquals(participant11.enrollment_date, None)
        
        participant11.enrollment_date = None
        self.assertRaises(Exception,
                          lambda: participant11.save())
        
        participant12.group = None
        self.assertRaises(Exception,
                          lambda: participant12.save())
    
    def testParticipantEnrollment(self):
        experiment1 = Experiment(name="Experiment 1")
        experiment1.save()
        experiment1.state = Experiment.ENABLED_STATE
        experiment1.save()
        experiment2 = Experiment(name="Experiment 2")
        experiment2.save()
        experiment2.state = Experiment.ENABLED_STATE
        experiment2.save()
        
        num_control1 = 0
        num_test1 = 0
        num_control2 = 0
        num_test2 = 0
        
        for i in range(1000):
            username="testuser%s" % i
            in_test1 = Experiment.test(experiment1.name, TestUser(username=username))
            self.assertEquals(in_test1, not Experiment.control(experiment1.name,
                                                               TestUser(username=username)))
            if in_test1:
                num_test1 += 1
            else:
                num_control1 += 1
            
            in_test2 = not Experiment.control(experiment2.name, TestUser(username=username))
            self.assertEquals(in_test2, Experiment.test(experiment2.name,
                                                        TestUser(username=username)))
            
            if in_test2:
                num_test2 += 1
            else:
                num_control2 += 1
        
        self.assert_(num_control1 > 400)
        self.assert_(num_control2 > 400)
        self.assert_(num_test1 > 400)
        self.assert_(num_test2 > 400)

    def testMissingGoalType(self):
        anonymous_visitor = AnonymousVisitor()
        anonymous_visitor.save()

        goal_type = GoalType(name="existing-goal")
        goal_type.save()
        
        nb_types = GoalType.objects.all().count()
        nb_records = GoalRecord.objects.all().count()

        GoalRecord.record('existing-goal', TestUser(anonymous_visitor=anonymous_visitor))
        self.assertEquals(nb_records + 1, GoalRecord.objects.all().count())
        self.assertEqual(nb_types, GoalType.objects.all().count())

        with patch(settings, 'LEAN_AUTOCREATE_GOAL_TYPES', False):
            GoalRecord.record('inexistant-goal', TestUser(anonymous_visitor=anonymous_visitor))
            self.assertEquals(nb_records + 1, GoalRecord.objects.all().count())
            self.assertEqual(nb_types, GoalType.objects.all().count())

        with patch(settings, 'LEAN_AUTOCREATE_GOAL_TYPES', NotImplemented):
            GoalRecord.record('inexistant-goal', TestUser(anonymous_visitor=anonymous_visitor))
            self.assertEquals(nb_records + 1, GoalRecord.objects.all().count())
            self.assertEqual(nb_types, GoalType.objects.all().count())
            
        with patch(settings, 'LEAN_AUTOCREATE_GOAL_TYPES', True):
            GoalRecord.record('inexistant-goal',
                              TestUser(anonymous_visitor=anonymous_visitor))
            self.assertEquals(nb_records + 2, GoalRecord.objects.all().count())
            self.assertEqual(nb_types + 1, GoalType.objects.all().count())
        

    def testGoals(self):
        anonymous_visitor = AnonymousVisitor()
        anonymous_visitor.save()
        
        # required fields for GoalType
        self.assertRaises(Exception, lambda: GoalType(name=None).save())
        
        goal_type = GoalType(name="test-goal")
        goal_type.save()
        
        # unique constraint on GoalType.name
        self.assertRaises(Exception, lambda: GoalType(name="test-goal").save())
        
        # required fields for GoalRecord
        self.assertRaises(Exception, lambda: GoalRecord().save())
        self.assertRaises(Exception, lambda: GoalRecord(anonymous_visitor=anonymous_visitor).save())
        self.assertRaises(Exception, lambda: GoalRecord(goal_type=goal_type).save())
        
        now = datetime.now()
        
        goal_record = GoalRecord(anonymous_visitor=anonymous_visitor, goal_type=goal_type)
        goal_record.save()
        
        self.assertTrue(goal_record.created >= now and goal_record.created <= datetime.now())
        
        # it's OK for the same user to record the same goal multiple times
        goal_record2 = GoalRecord(anonymous_visitor=anonymous_visitor, goal_type=goal_type)
        goal_record2.save()
        
        nb_records = GoalRecord.objects.all().count()
        GoalRecord.record('test-goal', TestUser())
        self.assertEquals(nb_records, GoalRecord.objects.all().count())
        GoalRecord.record('test-goal', TestUser(username='test'))
        self.assertEquals(nb_records, GoalRecord.objects.all().count())
        GoalRecord.record('test-goal', TestUser(anonymous_visitor=anonymous_visitor))
        self.assertEquals(nb_records + 1, GoalRecord.objects.all().count())
        GoalRecord.record('test-goal', TestUser(anonymous_visitor=anonymous_visitor))
        self.assertEquals(nb_records + 2, GoalRecord.objects.all().count())
    
    def testBotExclusion(self):
        experiment = Experiment(name="bot_experiment")
        experiment.save()
        experiment.state = Experiment.ENABLED_STATE
        experiment.save()
        
        user = TestUser(verified_human=False)
        participants_count = Participant.objects.all().count()
        in_test = Experiment.test(experiment.name, user)
        self.assertEquals(None, user.get_anonymous_id())
        self.assertEquals(participants_count, Participant.objects.all().count())
        
        enrollments = user.get_added_enrollments()
        self.assertEquals(len(enrollments.keys()), 1)
        self.assertTrue(experiment.name in enrollments.keys())
    
