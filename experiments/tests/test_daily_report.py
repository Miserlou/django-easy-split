# -*- coding: utf-8 -*-
import logging
l = logging.getLogger(__name__)

import mox

from datetime import date, datetime, time, timedelta

from django_lean.experiments.models import (Experiment, DailyEngagementReport,
                                            DailyConversionReport,
                                            DailyConversionReportGoalData,
                                            Participant, AnonymousVisitor,
                                            GoalType, GoalRecord)
from django_lean.experiments.reports import (EngagementReportGenerator,
                                             ConversionReportGenerator,
                                             calculate_participant_conversion,
                                             get_conversion_data,
                                             calculate_goal_type_conversion,
                                             find_experiment_group_participants)
from django_lean.experiments.tests.utils import create_user_in_group, TestCase


class TestDailyReports(TestCase):
    def setUp(self):
        self.experiment = Experiment(name="test_experiment")
        self.experiment.save()
        self.experiment.state = Experiment.ENABLED_STATE
        self.experiment.save()
        self.experiment.start_date = (self.experiment.start_date -
                                      timedelta(days=5))
        self.experiment.save()
        
        anonymous_visitor = AnonymousVisitor()
        anonymous_visitor.save()
        anonymous_participant = Participant(anonymous_visitor=anonymous_visitor,
                                            experiment=self.experiment,
                                            group=Participant.TEST_GROUP)
        anonymous_participant.save()
        anonymous_participant.enrollment_date = self.experiment.start_date
        anonymous_participant.save()
        
        self.other_experiment = Experiment(name="test_experiment2")
        self.other_experiment.save()
        self.other_experiment.state = Experiment.DISABLED_STATE
        self.other_experiment.save()
        self.other_experiment.start_date = (date.today() -
                                      timedelta(days=7))
        self.other_experiment.end_date = (date.today() -
                                      timedelta(days=3))
        self.other_experiment.save()
    
    def testDailyEngagementReport(self):
        users_test = []
        users_control = []
        
        num_control1 = 0
        num_test1 = 0
        num_control2 = 0
        num_test2 = 0
        
        #create users
        for i in range(5):
            users_control.append(create_user_in_group(self.experiment, i,
                                        Participant.CONTROL_GROUP,
                                        date.today() - timedelta(days=i)))
            users_test.append(create_user_in_group(self.experiment, i,
                                        Participant.TEST_GROUP,
                                        date.today() - timedelta(days=i)))
        
        # users_<test|control>[0] were enrolled today, [1] 1 day ago, etc.
        
        report_date = date.today() - timedelta(days=1)
        expected_engagement_score_calls = {
            (users_test[1], date.today() - timedelta(days=1), report_date): 3.2,
            (users_test[2], date.today() - timedelta(days=2), report_date): 2.5,
            (users_test[3], date.today() - timedelta(days=3), report_date): 4.1,
            (users_test[4], date.today() - timedelta(days=4), report_date): 0,
            (users_control[1], date.today() - timedelta(days=1), report_date): 0,
            (users_control[2], date.today() - timedelta(days=2), report_date): 0,
            (users_control[3], date.today() - timedelta(days=3), report_date): 0,
            (users_control[4], date.today() - timedelta(days=4), report_date): 0}
        
        test_case = self
        
        class EngagementScoreCalculatorStub(object):
            def calculate_user_engagement_score(self, user,
                                              start_date, end_date):
                test_case.assertNotEquals(user, None)
                test_case.assertTrue(expected_engagement_score_calls.
                                     has_key((user, start_date, end_date)))
                return expected_engagement_score_calls[(user,
                                                     start_date, end_date)]
        
        (EngagementReportGenerator(EngagementScoreCalculatorStub()).
           generate_daily_report_for_experiment(self.experiment, report_date))

        
        experiment_report = DailyEngagementReport.objects.get(
                                experiment=self.experiment, date=report_date)
        self.assertAlmostEqual((3.2 + 2.5 + 4.1 + 0)/4.0,
                                experiment_report.test_score)
        self.assertAlmostEqual(0.0, experiment_report.control_score)
        self.assertEquals(4, experiment_report.test_group_size)
        self.assertEquals(4, experiment_report.control_group_size)
        self.assertAlmostEqual(96.819293337188498, experiment_report.confidence)
    
    def testZeroParticipantExperiment(self):
        mocker = mox.Mox()
        engagement_calculator = mocker.CreateMockAnything()
        mocker.ReplayAll()
        
        report_date = date.today()
        EngagementReportGenerator(engagement_score_calculator=engagement_calculator).generate_daily_report_for_experiment(
            self.other_experiment, report_date)
        
        experiment_report = DailyEngagementReport.objects.get(
            experiment=self.other_experiment, date=report_date)
        
        mocker.VerifyAll()
        
        self.assertEquals(None, experiment_report.test_score)
        self.assertEquals(None, experiment_report.control_score)
        self.assertEquals(0, experiment_report.test_group_size)
        self.assertEquals(0, experiment_report.control_group_size)
    
    def testGenerateAllDailyEngagementReports(self):
        class DummyEngagementCalculator(object):
            def calculate_user_engagement_score(self, user, start_date, end_date):
                return 7
        engagement_report_generator = EngagementReportGenerator(engagement_score_calculator=DummyEngagementCalculator())
        engagement_report_generator.generate_daily_report_for_experiment(
                            self.experiment, date.today() - timedelta(days=2))
        engagement_report_generator.generate_daily_report_for_experiment(
                            self.experiment, date.today() - timedelta(days=3))
        engagement_report_generator.generate_all_daily_reports()
        DailyEngagementReport.objects.get(experiment=self.experiment,
                            date=date.today() - timedelta(days=1))
        DailyEngagementReport.objects.get(experiment=self.experiment,
                            date=date.today() - timedelta(days=2))
        DailyEngagementReport.objects.get(experiment=self.experiment,
                            date=date.today() - timedelta(days=3))
        DailyEngagementReport.objects.get(experiment=self.experiment,
                            date=date.today() - timedelta(days=4))
        DailyEngagementReport.objects.get(experiment=self.experiment,
                            date=date.today() - timedelta(days=5))
        self.assertEquals(5, DailyEngagementReport.objects.filter(
                                        experiment=self.experiment).count())
        DailyEngagementReport.objects.get(experiment=self.other_experiment,
                          date=date.today() - timedelta(days=3))
        DailyEngagementReport.objects.get(experiment=self.other_experiment,
                          date=date.today() - timedelta(days=4))
        DailyEngagementReport.objects.get(experiment=self.other_experiment,
                          date=date.today() - timedelta(days=5))
        DailyEngagementReport.objects.get(experiment=self.other_experiment,
                          date=date.today() - timedelta(days=6))
        DailyEngagementReport.objects.get(experiment=self.other_experiment,
                          date=date.today() - timedelta(days=7))
        
        self.assertEquals(5, DailyEngagementReport.objects.filter(
                                    experiment=self.other_experiment).count())
    
    def create_goal_record(self, record_datetime, anonymous_visitor, goal_type):
        record = GoalRecord.objects.create(anonymous_visitor=anonymous_visitor,
                                           goal_type=goal_type)
        record.created = record_datetime
        record.save()
    
    def create_participant(self, anonymous_visitor, experiment, enrollment_date, group):
        participant = Participant.objects.create(anonymous_visitor=anonymous_visitor,
                                                 experiment=experiment,
                                                 group=group)
        participant.enrollment_date=enrollment_date
        participant.save()
        return participant
    
    def testParticipantConversionCalculator(self):
        goal_types = [GoalType.objects.create(name=str(i)) for i in range(3)]
        anonymous_visitor = AnonymousVisitor.objects.create()
        participant = self.create_participant(
            anonymous_visitor=anonymous_visitor,
            experiment=self.experiment,
            enrollment_date=self.experiment.start_date + timedelta(days=2),
            group=Participant.TEST_GROUP)
        
        days = [datetime.combine(self.experiment.start_date + timedelta(days=i), time(hour=12))
                for i in range(5)]
        
        nb_goal_records = GoalRecord.objects.all().count()
        
        self.create_goal_record(days[0], anonymous_visitor, goal_types[0])
        self.create_goal_record(days[0], anonymous_visitor, goal_types[1])
        self.create_goal_record(days[1], anonymous_visitor, goal_types[0])
        self.create_goal_record(days[1], anonymous_visitor, goal_types[0])
        self.create_goal_record(days[2], anonymous_visitor, goal_types[1])
        self.create_goal_record(days[3], anonymous_visitor, goal_types[0])
        self.create_goal_record(days[4], anonymous_visitor, goal_types[0])
        self.create_goal_record(days[4], anonymous_visitor, goal_types[0])
        
        self.assertEquals(nb_goal_records + 8, GoalRecord.objects.all().count())
        
        # wasn't enrolled yet!
        self.assertEquals(calculate_participant_conversion(participant, goal_types[0], days[0]), 0)
        self.assertEquals(calculate_participant_conversion(participant, goal_types[1], days[0]), 0)
        self.assertEquals(calculate_participant_conversion(participant, goal_types[2], days[0]), 0)
        self.assertEquals(calculate_participant_conversion(participant, None, days[0]), 0)
        self.assertEquals(calculate_participant_conversion(participant, goal_types[0], days[1]), 0)
        self.assertEquals(calculate_participant_conversion(participant, goal_types[1], days[1]), 0)
        self.assertEquals(calculate_participant_conversion(participant, goal_types[2], days[1]), 0)
        self.assertEquals(calculate_participant_conversion(participant, None, days[1]), 0)
        
        # now enrolled
        self.assertEquals(calculate_participant_conversion(participant, goal_types[0], days[2]), 0)
        self.assertEquals(calculate_participant_conversion(participant, goal_types[1], days[2]), 1)
        self.assertEquals(calculate_participant_conversion(participant, goal_types[2], days[2]), 0)
        # "any" is one
        self.assertEquals(calculate_participant_conversion(participant, None, days[2]), 1)
        
        self.assertEquals(calculate_participant_conversion(participant, goal_types[0], days[3]), 1)
        self.assertEquals(calculate_participant_conversion(participant, goal_types[1], days[3]), 1)
        self.assertEquals(calculate_participant_conversion(participant, goal_types[2], days[3]), 0)
        # "any" is one, even though two different goals were achieved
        self.assertEquals(calculate_participant_conversion(participant, None, days[3]), 1)
        
        # there were three conversions on this day for goal 0, but we only count the first!
        self.assertEquals(calculate_participant_conversion(participant, goal_types[0], days[4]), 1)
        self.assertEquals(calculate_participant_conversion(participant, goal_types[1], days[4]), 1)
        self.assertEquals(calculate_participant_conversion(participant, goal_types[2], days[4]), 0)
        self.assertEquals(calculate_participant_conversion(participant, None, days[4]), 1)
    
    def testGoalTypeConversionCalculator(self):
        mocker = mox.Mox()
        participants = [mocker.CreateMockAnything(),
                        mocker.CreateMockAnything(),
                        mocker.CreateMockAnything()]
        goal_type = mocker.CreateMockAnything()
        report_date = mocker.CreateMockAnything()
        participant_conversion_calculator = mocker.CreateMockAnything()
        
        participant_conversion_calculator(
            participants[0], goal_type, report_date).InAnyOrder().AndReturn(1)
        participant_conversion_calculator(
            participants[1], goal_type, report_date).InAnyOrder().AndReturn(0)
        participant_conversion_calculator(
            participants[2], goal_type, report_date).InAnyOrder().AndReturn(1)
        
        mocker.ReplayAll()
        
        self.assertEquals(2, calculate_goal_type_conversion(
                goal_type, participants, report_date, participant_conversion_calculator))
        
        mocker.VerifyAll()
    
    def testExperimentGroupParticipantFinder(self):
        days = [datetime.combine(date.today() + timedelta(days=i), time(hour=12))
                for i in range(-7, 0)]
        
        experiment = Experiment(name="experiment1")
        experiment.save()
        experiment.state = Experiment.ENABLED_STATE
        experiment.save()
        experiment.start_date = days[2].date()
        experiment.save()
        
        other_experiment = Experiment(name="experiment2")
        other_experiment.save()
        other_experiment.state = Experiment.DISABLED_STATE
        other_experiment.save()
        other_experiment.start_date = days[0].date()
        other_experiment.end_date = days[4].date()
        other_experiment.save()
        
        anonymous_visitors = [AnonymousVisitor.objects.create() for i in range(10)]
        
        experiment_participant_groups = [
            [
                self.create_participant(anonymous_visitor=anonymous_visitors[0],
                                        experiment=experiment,
                                        enrollment_date=days[2],
                                        group=Participant.TEST_GROUP),
                self.create_participant(anonymous_visitor=anonymous_visitors[1],
                                        experiment=experiment,
                                        enrollment_date=days[2],
                                        group=Participant.CONTROL_GROUP),
                self.create_participant(anonymous_visitor=anonymous_visitors[3],
                                        experiment=experiment,
                                        enrollment_date=days[3],
                                        group=Participant.TEST_GROUP),
                self.create_participant(anonymous_visitor=anonymous_visitors[4],
                                        experiment=experiment,
                                        enrollment_date=days[4],
                                        group=Participant.CONTROL_GROUP),
                self.create_participant(anonymous_visitor=anonymous_visitors[6],
                                        experiment=experiment,
                                        enrollment_date=days[6],
                                        group=Participant.TEST_GROUP)
                ],
            [
                self.create_participant(anonymous_visitor=anonymous_visitors[0],
                                        experiment=other_experiment,
                                        enrollment_date=days[0],
                                        group=Participant.CONTROL_GROUP),
                self.create_participant(anonymous_visitor=anonymous_visitors[2],
                                        experiment=other_experiment,
                                        enrollment_date=days[0],
                                        group=Participant.TEST_GROUP),
                self.create_participant(anonymous_visitor=anonymous_visitors[5],
                                        experiment=other_experiment,
                                        enrollment_date=days[4],
                                        group=Participant.TEST_GROUP)
                ]
            ]
        
        ex1day2 = find_experiment_group_participants(Participant.TEST_GROUP, experiment, days[2])
        ex1day2visitors = [p.anonymous_visitor for p in ex1day2]
        self.assertTrue(anonymous_visitors[0] in ex1day2visitors)
        self.assertEquals(1, len(ex1day2visitors))
        
        ex1day4test = find_experiment_group_participants(Participant.TEST_GROUP, experiment, days[4])
        ex1day4testvisitors = [p.anonymous_visitor for p in ex1day4test]
        self.assertTrue(anonymous_visitors[0] in ex1day4testvisitors)
        self.assertTrue(anonymous_visitors[3] in ex1day4testvisitors)
        self.assertEquals(2, len(ex1day4testvisitors))
        
        ex1day4control = find_experiment_group_participants(Participant.CONTROL_GROUP, experiment, days[4])
        ex1day4controlvisitors = [p.anonymous_visitor for p in ex1day4control]
        self.assertTrue(anonymous_visitors[1] in ex1day4controlvisitors)
        self.assertTrue(anonymous_visitors[4] in ex1day4controlvisitors)
        self.assertEquals(2, len(ex1day4controlvisitors))
        
        ex2day5test = find_experiment_group_participants(Participant.TEST_GROUP, other_experiment, days[5])
        ex2day5testvisitors = [p.anonymous_visitor for p in ex2day5test]
        self.assertTrue(anonymous_visitors[2] in ex2day5testvisitors)
        self.assertTrue(anonymous_visitors[5] in ex2day5testvisitors)
        self.assertEquals(2, len(ex2day5testvisitors))
    
    def testGetConversionData(self):
        days = [datetime.combine(date.today() + timedelta(days=i), time(hour=12))
                for i in range(-7, 0)]
        
        yesterday = date.today() - timedelta(days=1)
        experiment = Experiment(name="experiment1")
        experiment.save()
        experiment.state = Experiment.ENABLED_STATE
        experiment.save()
        experiment.start_date = yesterday
        experiment.save()
        
        goal_types = [GoalType.objects.create(name="%s" % i) for i in range(4)]
        
        report = DailyConversionReport.objects.create(experiment=experiment,
                                             date=yesterday,
                                             overall_test_conversion=17,
                                             overall_control_conversion=12,
                                             test_group_size=139,
                                             control_group_size=142,
                                             confidence=87.3)
        
        DailyConversionReportGoalData.objects.create(report=report,
                                                     goal_type=goal_types[0],
                                                     test_conversion=11,
                                                     control_conversion=0,
                                                     confidence=65.3)
        DailyConversionReportGoalData.objects.create(report=report,
                                                     goal_type=goal_types[1],
                                                     test_conversion=0,
                                                     control_conversion=21,
                                                     confidence=None)
        DailyConversionReportGoalData.objects.create(report=report,
                                                     goal_type=goal_types[2],
                                                     test_conversion=23,
                                                     control_conversion=21,
                                                     confidence=100)
        
        data = get_conversion_data(experiment, yesterday)
        
        self.assertEquals(data['date'], yesterday)
        self.assertTrue("totals" in data)
        self.assertTrue("goal_types" in data)
        self.assertEquals(4, len(data["goal_types"].keys()))
        
        for goal_type in goal_types[0:3]:
            self.assertTrue(goal_type.name in data["goal_types"])
            
            goal_type_data = data["goal_types"][goal_type.name]
            self.assertTrue("test_count" in goal_type_data)
            self.assertTrue("control_count" in goal_type_data)
            self.assertTrue("test_rate" in goal_type_data)
            self.assertTrue("control_rate" in goal_type_data)
            self.assertTrue("improvement" in goal_type_data)
            self.assertTrue("confidence" in goal_type_data)
        
        self.assertEquals(None, data["goal_types"][goal_types[3].name])
        
        self.assertEquals(139, data["test_group_size"])
        self.assertEquals(142, data["control_group_size"])
        
        totals = data["totals"]
        
        expected_test_rate = 17. / 139. * 100.
        expected_control_rate = 12. / 142. * 100.
        expected_improvement = (expected_test_rate - expected_control_rate) / expected_control_rate * 100.
        
        self.assertAlmostEquals(expected_test_rate, totals["test_rate"])
        self.assertAlmostEquals(expected_control_rate, totals["control_rate"])
        self.assertAlmostEquals(expected_improvement, totals["improvement"])
        self.assertAlmostEquals(87.3, totals["confidence"])
        self.assertEquals(17, totals["test_count"])
        self.assertEquals(12, totals["control_count"])
        
        self.assertEquals(0, data["goal_types"][goal_types[0].name]["control_rate"])
        self.assertAlmostEquals(11./139*100., data["goal_types"][goal_types[0].name]["test_rate"])
        self.assertEquals(None, data["goal_types"][goal_types[0].name]["improvement"])
        self.assertAlmostEquals(65.3, data["goal_types"][goal_types[0].name]["confidence"])
        self.assertEquals(11, data["goal_types"][goal_types[0].name]["test_count"])
        self.assertEquals(0, data["goal_types"][goal_types[0].name]["control_count"])
        
        self.assertAlmostEquals(21./142*100., data["goal_types"][goal_types[1].name]["control_rate"])
        self.assertEquals(None, data["goal_types"][goal_types[1].name]["confidence"])
        self.assertEquals(None, data["goal_types"][goal_types[1].name]["improvement"])
        
        self.assertAlmostEquals((23./139-21./142)/(21./142)*100.,
                                data["goal_types"][goal_types[2].name]["improvement"])


#TODO test with zero participants and check rate == None

#TODO sometimes confidence cannot be calculated and must return None. Add a test to verify this.
    
    def testConversionReportGenerator(self):
        days = [datetime.combine(date.today() + timedelta(days=i), time(hour=12))
                for i in range(-7, 0)]
        
        experiment = Experiment(name="experiment1")
        experiment.save()
        experiment.state = Experiment.ENABLED_STATE
        experiment.save()
        experiment.start_date = days[2].date()
        experiment.save()
        
        other_experiment = Experiment(name="experiment2")
        other_experiment.save()
        other_experiment.state = Experiment.DISABLED_STATE
        other_experiment.save()
        other_experiment.start_date = days[0].date()
        other_experiment.end_date = days[4].date()
        other_experiment.save()

        
        goal_types = [GoalType.objects.create(name="%s" % i) for i in range(3)]
        
        # experiment starts on days[2]
        # other experiment starts on days[0]
        
        mocker = mox.Mox()
        finder = mocker.CreateMockAnything()
        calculator = mocker.CreateMockAnything()
        
        default_data = {
            Participant.TEST_GROUP: {
                "count": 110,
                "conversions": [23, 12, 9]
            },
            Participant.CONTROL_GROUP: {
                "count": 130,
                "conversions": [12, 47, 5]
                }
            }
        day_2_data = {
            Participant.TEST_GROUP: {
                "count": 12,
                "conversions": [0, 2, 3]
                },
            Participant.CONTROL_GROUP: {
                "count": 7,
                "conversions": [1, 0, 3]
                }
            }
        day_3_data = {
            Participant.TEST_GROUP: {
                "count": 5,
                "conversions": [1, 0, 3]
                },
            Participant.CONTROL_GROUP: {
                "count": 12,
                "conversions": [0, 0, 0]
                }
            }
        day_4_data = {
            Participant.TEST_GROUP: {
                "count": 0,
                "conversions": [0, 0, 0]
                },
            Participant.CONTROL_GROUP: {
                "count": 25,
                "conversions": [2, 3, 7]
                }
            }
        
        for day in days[2:7]:
            data = default_data
            if day == days[2]:
                data = day_2_data
            if day == days[3]:
                data = day_3_data
            if day == days[4]:
                data = day_4_data
            
            for group in (Participant.TEST_GROUP, Participant.CONTROL_GROUP):
                mock_participants = mocker.CreateMockAnything()
                finder(group, experiment, day.date()).InAnyOrder().AndReturn(mock_participants)
                mock_participants.count().MultipleTimes().AndReturn(data[group]["count"])
                for goal_type in goal_types:
                    calculator(goal_type, mock_participants, day.date()).InAnyOrder().AndReturn(data[group]["conversions"][int(goal_type.name)])
                calculator(None, mock_participants, day.date()).InAnyOrder().AndReturn(sum(data[group]["conversions"]))
        mocker.ReplayAll()
        
        for d in days[2:7]:
            ConversionReportGenerator(calculator, finder).generate_daily_report_for_experiment(
                experiment, d.date())
        
        results = DailyConversionReport.objects.filter(
            experiment=experiment).order_by('-date')
        
        mocker.VerifyAll()
        
        self.assertEquals(results.count(), 5)
        report_days = [ d.date() for d in days[2:7]]
        for i in range(5):
            self.assertEquals(results[i].date, report_days[4-i])
        
        # Day 2
        self.assertEquals(12, results[4].test_group_size)
        self.assertEquals(7, results[4].control_group_size)
        self.assertEquals(5, results[4].overall_test_conversion)
        self.assertEquals(4, results[4].overall_control_conversion)
        
        day_2_goal_4_test_conversion = DailyConversionReportGoalData.objects.filter(
            report=results[4],
            goal_type=goal_types[0])[0].test_conversion
        self.assertEquals(0, day_2_goal_4_test_conversion)
        
        day_2_goal_2_control_conversion = DailyConversionReportGoalData.objects.filter(
            report=results[4],
            goal_type=goal_types[2])[0].control_conversion
        self.assertEquals(3, day_2_goal_2_control_conversion)
        
        # Day 3
        self.assertEquals(5, results[3].test_group_size)
        # Day 4
        self.assertEquals(0, results[2].test_group_size)
        self.assertEquals(None, results[2].confidence)
        day_4_goal_1_confidence = DailyConversionReportGoalData.objects.filter(
            report=results[2],
            goal_type=goal_types[0])[0].confidence
        self.assertEquals(None, day_4_goal_1_confidence)
        # Day 5
        day_5_goal_0_confidence = DailyConversionReportGoalData.objects.filter(
            report=results[1],
            goal_type=goal_types[0])[0].confidence
        self.assertAlmostEqual(98.935467172597029, day_5_goal_0_confidence, places=6)
    
