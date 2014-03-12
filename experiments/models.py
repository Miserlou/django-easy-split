# -*- coding: utf-8 -*-
import logging
l = logging.getLogger(__name__)

from datetime import date
import random

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.core.exceptions import ObjectDoesNotExist

from django_lean.experiments.signals import goal_recorded, user_enrolled


class AnonymousVisitor(models.Model):
    """An anonymous visitor"""
    created = models.DateTimeField(auto_now_add=True, db_index=True)


class GoalType(models.Model):
    """Defines a type of goal."""
    name = models.CharField(max_length=128, unique=True)

    def __unicode__(self):
        return self.name


class GoalRecord(models.Model):
    """Records a discreet goal achievement."""
    created = models.DateTimeField(auto_now_add=True, db_index=True)
    anonymous_visitor = models.ForeignKey(AnonymousVisitor)
    goal_type = models.ForeignKey(GoalType)

    @classmethod
    def _record(cls, goal_name, experiment_user):
        """
        Records a goal achievement for the experiment user.
        If the user does not have an anonymous visitor ID, does nothing.
        If the goal name is not known, throws an Exception.
        """
        anonymous_id = experiment_user.get_anonymous_id()
        if anonymous_id:
            anonymous_visitor = AnonymousVisitor.objects.get(id=anonymous_id)
            if getattr(settings, 'LEAN_AUTOCREATE_GOAL_TYPES', False):
                (goal_type, created) = GoalType.objects.get_or_create(name=goal_name)
            else:
                goal_type = GoalType.objects.get(name=goal_name)

            goal_record = GoalRecord.objects.create(
                goal_type=goal_type, anonymous_visitor=anonymous_visitor
            )
            goal_recorded.send(sender=cls, goal_record=goal_record,
                               experiment_user=experiment_user)
            return goal_record

    @classmethod
    def record(cls, goal_name, experiment_user):
        try:
            return cls._record(goal_name, experiment_user)
        except GoalType.DoesNotExist:
            if settings.DEBUG:
                raise
            l.warning("Can't find the GoalType named %s" % goal_name)
        except Exception, e:
            l.exception("Unexpected exception in GoalRecord.record")


class Experiment(models.Model):
    """ Defines a split testing experiment"""
    class __UnverifiedUser(object):
        def __init__(self, experiment_user):
            self.experiment_user = experiment_user

        def get_enrollment(self, experiment):
            return self.experiment_user.get_temporary_enrollment(
                experiment.name)

        def set_enrollment(self, experiment, group_id):
            self.experiment_user.store_temporary_enrollment(experiment.name,
                                                            group_id)
            user_enrolled.send(sender=self.__class__,
                               experiment=experiment,
                               experiment_user=self.experiment_user,
                               group_id=group_id)

    class __RegisteredUser(object):
        def __init__(self, experiment_user):
            self.experiment_user = experiment_user

        def get_enrollment(self, experiment):
            participants = Participant.objects.filter(
                user=self.experiment_user.get_registered_user(),
                experiment=experiment)
            if participants.count() == 1:
                return participants[0].group

        def set_enrollment(self, experiment, group_id):
            participant = Participant.objects.create(
                user=self.experiment_user.get_registered_user(),
                experiment=experiment, group=group_id
            )
            user_enrolled.send(sender=self.__class__,
                               experiment=experiment,
                               experiment_user=self.experiment_user,
                               group_id=group_id)

    class __AnonymousUser(object):
        def __init__(self, experiment_user):
            self.experiment_user = experiment_user

        def __get_anonymous_visitor(self):
            anonymous_id = self.experiment_user.get_anonymous_id()
            if anonymous_id:
                anonymous_visitors = AnonymousVisitor.objects.filter(id=anonymous_id)
                if anonymous_visitors.count() == 1:
                    return anonymous_visitors[0]

        def get_enrollment(self, experiment):
            anonymous_visitor = self.__get_anonymous_visitor()

            if anonymous_visitor:
                participants = Participant.objects.filter(
                    anonymous_visitor=anonymous_visitor,
                    experiment=experiment)
                if participants.count() == 1:
                    return participants[0].group

        def set_enrollment(self, experiment, group_id):
            anonymous_visitor = self.__get_anonymous_visitor()
            if not anonymous_visitor:
                anonymous_visitor = AnonymousVisitor()
                anonymous_visitor.save()
                self.experiment_user.set_anonymous_id(anonymous_visitor.id)

            Participant.objects.create(
                anonymous_visitor=anonymous_visitor,
                experiment=experiment, group=group_id
            )
            user_enrolled.send(sender=self.__class__,
                               experiment=experiment,
                               experiment_user=self.experiment_user,
                               group_id=group_id)

    @classmethod
    def __create_user(cls, experiment_user):
        if not experiment_user.is_anonymous():
            return cls.__RegisteredUser(experiment_user)
        if not experiment_user.is_verified_human():
            return cls.__UnverifiedUser(experiment_user)
        else:
            return cls.__AnonymousUser(experiment_user)

    DISABLED_STATE = 0
    ENABLED_STATE = 1
    PROMOTED_STATE = 2

    STATES = (
        (DISABLED_STATE, 'Disabled'),
        (ENABLED_STATE, 'Enabled'),
        (PROMOTED_STATE, 'Promoted'))

    name = models.CharField(unique=True, max_length=128)
    state = models.IntegerField(default=DISABLED_STATE, choices=STATES)
    start_date = models.DateField(blank=True, null=True, db_index=True)
    end_date = models.DateField(blank=True, null=True)

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        """
        The save override's goal is to save the start or end date when
        the state changes
        """
        #do nothing for new ones
        if self.id:
            old_self = None

            try:
                old_self = Experiment.objects.get(id=self.id)
            except Experiment.DoesNotExist:
                raise Exception("Can't find the existing Experiment.")

            if old_self.state != self.state:
                if (old_self.state == Experiment.DISABLED_STATE
                    and self.state == Experiment.ENABLED_STATE
                    and not old_self.start_date):
                    # enabling
                    self.start_date = date.today()
                elif (old_self.state == Experiment.ENABLED_STATE
                      and self.state == Experiment.DISABLED_STATE
                      and not old_self.end_date):
                    # disabling
                    self.end_date = date.today()
                elif (old_self.state == Experiment.ENABLED_STATE
                      and self.state == Experiment.PROMOTED_STATE
                      and not old_self.end_date):
                    #promoting
                    self.end_date = date.today()
        return super(Experiment, self).save(*args, **kwargs)

    @staticmethod
    def control(experiment_name, experiment_user):
        """
        Will return True when user is part of the control group in
        the passed experiment. If the user is not enrolled in this
        experiment, and the experiment is enabled, it will enroll the user.
        """
        return Experiment.__test_group(experiment_name, experiment_user,
                                       Participant.CONTROL_GROUP)

    @staticmethod
    def test(experiment_name, experiment_user):
        """
        Will return True when user is part of the test group in
        the passed experiment. If the user is not enrolled in this
        experiment, and the experiment is enabled, it will enroll the user.
        """
        return Experiment.__test_group(experiment_name, experiment_user,
                                       Participant.TEST_GROUP)

    @classmethod
    def __test_group(cls, experiment_name, experiment_user, queried_group):
        """does the real work"""
        from django_lean.experiments.loader import ExperimentLoader
        ExperimentLoader.load_all_experiments()

        experiment = None
        try:
            experiment = Experiment.objects.get(name=experiment_name)
        except Experiment.DoesNotExist:
            if settings.DEBUG:
                raise Exception("Can't find the Experiment named %s" %
                                experiment_name)
            else:
                l.warning("Can't find the Experiment named %s" %
                          experiment_name)
                return queried_group == Participant.CONTROL_GROUP
        if experiment.state == Experiment.DISABLED_STATE:
            return queried_group == Participant.CONTROL_GROUP
        elif experiment.state == Experiment.PROMOTED_STATE:
            return queried_group == Participant.TEST_GROUP

        if experiment.state != Experiment.ENABLED_STATE:
            raise Exception("Invalid experiment state !")

        user = cls.__create_user(experiment_user)

        assigned_group = user.get_enrollment(experiment)

        if assigned_group == None:
            assigned_group = random.choice((Participant.CONTROL_GROUP,
                                            Participant.TEST_GROUP))
            user.set_enrollment(experiment, assigned_group)

        return queried_group == assigned_group


class Participant(models.Model):
    """A participant in a split testing experiment """

    class Meta:
        unique_together= (('user', 'experiment'),
                          ('anonymous_visitor', 'experiment'))

    CONTROL_GROUP = 0
    TEST_GROUP = 1

    GROUPS = (
        (CONTROL_GROUP, "Control"),
        (TEST_GROUP, "Test"))

    user = models.ForeignKey(User, null=True)
    experiment = models.ForeignKey(Experiment)
    enrollment_date = models.DateField(db_index=True, auto_now_add=True)
    group = models.IntegerField(choices=GROUPS)
    anonymous_visitor = models.ForeignKey(AnonymousVisitor, null=True, blank=True)

    def __unicode__(self):
        if self.user: # can be null
            username = self.user.username
        else:
            username = 'anonymous#%d' % self.anonymous_visitor.id
        return "%s %s" % (username, self.group)

    def __init__(self, *args, **kwargs):
        super(Participant, self).__init__(*args, **kwargs)
        if not self.id:
            if (not self.anonymous_visitor) == (not self.user):
                raise Exception("Participants require exactly one of "
                                "`anonymous_visitor` or `user`.")


class DailyEngagementReport(models.Model):
    """Hold the scores for a given experiment on a given day"""
    date = models.DateField(db_index=True)
    experiment = models.ForeignKey(Experiment)
    test_score = models.FloatField(null=True)
    control_score = models.FloatField(null=True)
    test_group_size = models.IntegerField()
    control_group_size = models.IntegerField()
    confidence = models.FloatField(null=True)


class DailyConversionReport(models.Model):
    """Stores the daily conversion scores."""
    date = models.DateField(db_index=True)
    experiment = models.ForeignKey(Experiment)
    overall_test_conversion = models.IntegerField()
    overall_control_conversion = models.IntegerField()
    test_group_size = models.IntegerField()
    control_group_size = models.IntegerField()
    confidence = models.FloatField(null=True)


class  DailyConversionReportGoalData(models.Model):
    """Stores the daily conversion report goal data."""
    report = models.ForeignKey(DailyConversionReport, related_name="goal_data")
    goal_type = models.ForeignKey(GoalType)
    test_conversion = models.IntegerField()
    control_conversion = models.IntegerField()
    confidence = models.FloatField(null=True)
