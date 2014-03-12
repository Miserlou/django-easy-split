# -*- coding: utf-8 -*-
import logging
l = logging.getLogger(__name__)

from datetime import datetime, timedelta

from django_lean.experiments.models import (DailyEngagementReport,
                                            DailyConversionReport,
                                            DailyConversionReportGoalData,
                                            Experiment, Participant,
                                            GoalRecord, GoalType)
from django_lean.experiments.significance import chi_square_p_value


def calculate_participant_conversion(participant, goal_type, report_date):
    """
    Determines whether a specific participant achieved a specific goal_type
    between the participant's enrollment date and the report date.
    If goal_type is None, then it determines the result for _any_ goal_type.
    """
    if goal_type == None:
        count = GoalRecord.objects.filter(
            created__gte=participant.enrollment_date,
            created__lt=(report_date + timedelta(days=1)),
            anonymous_visitor=participant.anonymous_visitor).count()
    else:
        count = GoalRecord.objects.filter(
            goal_type=goal_type,
            created__gte=participant.enrollment_date,
            created__lt=(report_date + timedelta(days=1)),
            anonymous_visitor=participant.anonymous_visitor).count()
    
    return count and 1 or 0

def calculate_goal_type_conversion(goal_type,
                                   participants,
                                   report_date,
                                   participant_conversion_calculator=calculate_participant_conversion):
    """
    Calculates the number of conversions for a specific goal type among the group of
    participants between each participant's enrollment date and the given report date.
    """
    count = 0
    for participant in participants:
        count += participant_conversion_calculator(participant, goal_type, report_date)
    return count

def find_experiment_group_participants(group, experiment, report_date):
    """
    Returns a collection of participants belonging to the specified group in the
    given experiment. It only includes participants that were enrolled in the
    given report date.
    """
    return Participant.objects.filter(group=group,
                                      enrollment_date__lte=report_date,
                                      experiment=experiment,
                                      anonymous_visitor__isnull=False)

def __rate(a, b):
    if not b or a == None:
        return None
    return 100. * a / b

def __improvement(a, b):
    if not b or not a:
        return None
    return (a - b) * 100. / b

def get_conversion_data(experiment, date):
    """
    Returns (if report exists):
    {
      "date",
      "test_group_size",
      "control_group_size",
      "goal_types": {
        <goal_type_name>: {
          "test_count",
          "control_count",
          "test_rate",
          "control_rate",
          "improvement",
          "confidence"
        }, ...
      },
      "totals": {
        "test_count",
        "control_count",
        "test_rate",
        "control_rate",
        "improvement",
        "confidence"
      }
    }
    
    Otherwise, returns 'None'
    
    <goal_type_name> will map to None if a report was generated for a given day, but no goal type report was generated for <goal_type_name>
    """
    report_set = DailyConversionReport.objects.filter(experiment=experiment, date=date)
    if report_set.count() != 1:
        l.warn("No conversion report for date %s and experiment %s" %
               (date, experiment.name))
        return None
    
    report = report_set[0]
    test_rate = __rate(report.overall_test_conversion, report.test_group_size)
    control_rate = __rate(report.overall_control_conversion, report.control_group_size)
    improvement = __improvement(test_rate, control_rate)
    
    all_goal_types = GoalType.objects.all()
    
    goal_types_data = {}
    for goal_type in all_goal_types:
        goal_type_data_set = report.goal_data.filter(goal_type=goal_type)
        if goal_type_data_set.count() != 1:
            goal_data = None
        else:
            goal_type_data = goal_type_data_set[0]
            goal_test_rate = __rate(goal_type_data.test_conversion, report.test_group_size)
            goal_control_rate = __rate(goal_type_data.control_conversion, report.control_group_size)
            goal_improvement = __improvement(goal_test_rate, goal_control_rate)
            goal_data = {
                "test_count": goal_type_data.test_conversion,
                "control_count": goal_type_data.control_conversion,
                "test_rate": goal_test_rate,
                "control_rate": goal_control_rate,
                "improvement": goal_improvement,
                "confidence": goal_type_data.confidence
                }
        goal_types_data[goal_type.name] = goal_data
    data = {
        "date": report.date,
        "test_group_size": report.test_group_size,
        "control_group_size": report.control_group_size,
        "goal_types": goal_types_data,
        "totals": {
            "test_count": report.overall_test_conversion,
            "control_count": report.overall_control_conversion,
            "test_rate": test_rate,
            "control_rate": control_rate,
            "improvement": improvement,
            "confidence": report.confidence
            }
        }
    return data

class BaseReportGenerator(object):
    def __init__(self, report_model_class):
        self.report_model_class = report_model_class
    
    def generate_all_daily_reports(self):
        """ Generates all missing reports up until yesterday """
        experiments = Experiment.objects.filter(start_date__isnull=False)
        yesterday = (datetime.today() - timedelta(days=1)).date()
        for experiment in experiments:
            start_date = experiment.start_date
            current_date = start_date
            end_date = experiment.end_date or yesterday
            end_date = min(end_date, yesterday)
            
            # get or create the report for all the days of the experiment
            while current_date <= end_date:
                if (self.report_model_class.objects.filter(
                        experiment=experiment, date=current_date).count() == 0):
                    daily_report = self.generate_daily_report_for_experiment(
                        experiment=experiment, report_date=current_date)
                current_date = current_date + timedelta(days=1)
    

class ConversionReportGenerator(BaseReportGenerator):
    def __init__(self, goal_type_conversion_calculator=calculate_goal_type_conversion,
                 participant_finder=find_experiment_group_participants):
        BaseReportGenerator.__init__(self, DailyConversionReport)
        self.goal_type_conversion_calculator = goal_type_conversion_calculator
        self.participant_finder = participant_finder
    
    def __confidence(self, a_count, a_conversion, b_count, b_conversion):
        contingency_table = [[a_count - a_conversion, a_conversion],
                             [b_count - b_conversion, b_conversion]]
    
        chi_square, p_value = chi_square_p_value(contingency_table)
        if p_value:
            return (1 - p_value) * 100
        else:
            return None
    
    def generate_daily_report_for_experiment(self, experiment, report_date):
        """ Generates a single conversion report """
        control_participants = self.participant_finder(Participant.CONTROL_GROUP,
                                                       experiment, report_date)
        test_participants = self.participant_finder(Participant.TEST_GROUP,
                                                    experiment, report_date)
        control_participant_count = control_participants.count()
        test_participant_count = test_participants.count()
        
        total_control_conversion = self.goal_type_conversion_calculator(
            None, control_participants, report_date)
        total_test_conversion = self.goal_type_conversion_calculator(
            None, test_participants, report_date)
        
        confidence = self.__confidence(test_participant_count, total_test_conversion,
                                       control_participant_count, total_control_conversion)
        
        report = DailyConversionReport.objects.create(
            experiment=experiment,
            date=report_date,
            test_group_size=test_participant_count,
            control_group_size=control_participant_count,
            overall_test_conversion=total_test_conversion,
            overall_control_conversion=total_control_conversion,
            confidence=confidence)
        
        for goal_type in GoalType.objects.all():
            control_count = self.goal_type_conversion_calculator(goal_type,
                                                                 control_participants,
                                                                 report_date)
            test_count = self.goal_type_conversion_calculator(goal_type,
                                                              test_participants,
                                                              report_date)
            confidence = self.__confidence(test_participant_count, test_count,
                                           control_participant_count, control_count)
            DailyConversionReportGoalData.objects.create(
                report=report, goal_type=goal_type,
                test_conversion=test_count,
                control_conversion=control_count,
                confidence=confidence)
    

class EngagementReportGenerator(BaseReportGenerator):
    def __init__(self, engagement_score_calculator):
        BaseReportGenerator.__init__(self, DailyEngagementReport)
        self.engagement_score_calculator = engagement_score_calculator
    
    def __generate_scores(self, experiment, group, report_date):
        """
        Returns an array of all scores for participants in the given group in the
        given experiment, as of the specified report date.
        """
        participants = Participant.objects.filter(
                            experiment=experiment,
                            group=group,
                            enrollment_date__lte=report_date).exclude(user=None)
        scores = []
        for participant in participants:
            scores.append(self.engagement_score_calculator.
                          calculate_user_engagement_score(participant.user,
                                                          participant.enrollment_date,
                                                          report_date))
        return scores
    
    def generate_daily_report_for_experiment(self, experiment, report_date):
        """ Generates a single engagement report """
        try:
            from numpy import mean, isnan
            from scipy.stats import ttest_ind
        except ImportError:
            from django_lean.experiments.stats import mean, isnan, ttest_ind 
        test_group_scores = self.__generate_scores(
            experiment, Participant.TEST_GROUP, report_date)
        control_group_scores = self.__generate_scores(
            experiment, Participant.CONTROL_GROUP, report_date)
        
        test_group_mean = None
        control_group_mean = None
        confidence = None
        
        if len(test_group_scores):
            test_group_mean = mean(test_group_scores)
        if len(control_group_scores):
            control_group_mean = mean(control_group_scores)
        if len(test_group_scores) and len(control_group_scores):
            t_value, p_value = ttest_ind(test_group_scores, control_group_scores)
            if isnan(p_value):
                confidence = None
            else:
                confidence = (1 - p_value) * 100
        
        DailyEngagementReport.objects.create(
            experiment=experiment,
            date=report_date,
            test_score=test_group_mean,
            control_score=control_group_mean,
            test_group_size=len(test_group_scores),
            control_group_size=len(control_group_scores),
            confidence=confidence)
    
