# -*- coding: utf-8 -*-
import logging
l = logging.getLogger(__name__)

from contextlib import contextmanager

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase as DjangoTestCase
from django.utils.importlib import import_module
from django.utils.functional import LazyObject

from django_lean.experiments.loader import ExperimentLoader
from django_lean.experiments.models import Participant
from django_lean.lean_analytics import reset_caches


def get_session(session_key):
    engine = import_module(settings.SESSION_ENGINE)
    session = engine.SessionStore(session_key)
    session.load()
    return session

def create_user_in_group(experiment, i, group, enrollment_date):
    user = User(username="user%s_%s" % (i, group),
                email="email%s_%s@example.com" % (i, group))
    user.save()
    experiment_participant = Participant(user=user,
                                         experiment=experiment,
                                         group=group)
    experiment_participant.save()
    experiment_participant.enrollment_date = enrollment_date
    experiment_participant.save()
    return user

class TestCase(DjangoTestCase):
    def _pre_setup(self):
        super(TestCase, self)._pre_setup()
        experiments = getattr(self, 'experiments', [])
        ExperimentLoader.load_all_experiments(apps=experiments)
        self.original_LEAN_ANALYTICS = settings.LEAN_ANALYTICS
        settings.LEAN_ANALYTICS = []
        reset_caches()

    def _post_teardown(self):
        settings.LEAN_ANALYTICS = self.original_LEAN_ANALYTICS
        super(TestCase, self)._post_teardown()


class TestUser(object):
    """
    A utility class for testing that implements an 'ExperimentUser' object
    useful in tests.
    """
    def __init__(self, username=None, anonymous_visitor=None,
                 verified_human=True):
        if anonymous_visitor:
            self.anonymous_id = anonymous_visitor.id
        else:
            self.anonymous_id = None
        
        if not username == None:
            self.user, created = User.objects.get_or_create(
                username=username, email="%s@example.com" % username)
        else:
            self.user = None
        
        self.verified_human = verified_human
        self.session = {}
        self.temporary_enrollments = {}
    
    def is_anonymous(self):
        return self.user == None
    
    def set_anonymous_id(self, anonymous_id):
        self.anonymous_id = anonymous_id
    
    def get_anonymous_id(self):
        return self.anonymous_id
    
    def get_registered_user(self):
        return self.user
    
    def is_verified_human(self):
        return self.verified_human
    
    def store_temporary_enrollment(self, experiment_name, group_id):
        self.temporary_enrollments[experiment_name] = group_id
    
    def get_added_enrollments(self):
        return self.temporary_enrollments
    
    def get_temporary_enrollment(self, experiment_name):
        added_enrollments = self.get_added_enrollments()
        if not added_enrollments:
            return None
        else:
            return added_enrollments.get(experiment_name)
    
@contextmanager
def patch(namespace, name, value):
    """Patches `namespace`.`name` with `value`."""
    if isinstance(namespace, LazyObject):
        if namespace._wrapped is None:
            namespace._setup()
        namespace = namespace._wrapped

    try:
        original = getattr(namespace, name)
    except AttributeError:
        original = NotImplemented
    try:
        if value is NotImplemented:
            if original is not NotImplemented:
                delattr(namespace, name)
        else:
            setattr(namespace, name, value)
        yield
    finally:
        if original is NotImplemented:
            if value is not NotImplemented:
                delattr(namespace, name)
        else:
            setattr(namespace, name, original) 
