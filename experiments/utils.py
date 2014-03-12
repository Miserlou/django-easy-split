from contextlib import contextmanager

from django.contrib.sites.models import Site
from django.core import mail
from django.db import transaction
from django.utils.functional import LazyObject


def get_current_site():
    if Site._meta.installed:
        return Site.objects.get_current()
    return None

def in_transaction(test_ignore=True):
    result = transaction.is_managed()
    if test_ignore:
        # Ignore when running inside a Django test case, which uses
        # transactions.
        result = result and not hasattr(mail, 'outbox')
    return result


@contextmanager
def patch(namespace, name, function):
    """Patches `namespace`.`name` with `function`."""
    if isinstance(namespace, LazyObject):
        if namespace._wrapped is None:
            namespace._setup()
        namespace = namespace._wrapped
    try:
        original = getattr(namespace, name)
    except AttributeError:
        original = NotImplemented
    try:
        setattr(namespace, name, function)
        yield
    finally:
        if original is NotImplemented:
            delattr(namespace, name)
        else:
            setattr(namespace, name, original)
