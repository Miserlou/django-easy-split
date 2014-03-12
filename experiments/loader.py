# -*- coding: utf-8 -*-
import logging, os, sys
l = logging.getLogger(__name__)

from django.conf import settings
from django.utils import simplejson

from django_lean.experiments.models import Experiment

class ExperimentLoader(object):
    """
    Loads the experiments from a file containing a list of experiment
    It will add new experiments, but not touch existing experiments
    """
    NAME_ATTRIBUTE="name"
    ALLOWED_ATTRIBUTES=[NAME_ATTRIBUTE]
    APPLICATION_RELATIVE_EXPERIMENT_FILE = "%sexperiments.json" % os.sep
    __loaded = False

    @classmethod
    def load_all_experiments(cls, apps=settings.INSTALLED_APPS):
        """
        Loads experiments for all applications in settings.INSTALLED_APPS
        """
        if not cls.__loaded:
            cls.__loaded = True
            for app_name in apps:
                application_path = os.path.dirname(sys.modules[app_name].__file__)
                application_experiment_file_path = (
                    application_path +
                    ExperimentLoader.APPLICATION_RELATIVE_EXPERIMENT_FILE)
                if os.access(application_experiment_file_path, os.F_OK):
                    ExperimentLoader.load_experiments(application_experiment_file_path)
    
    @staticmethod
    def load_experiments(filename):
        """
        Will load the data from the filename, expected data format to be
        JSON : [{ name : "name" }]
        """
        fp = open(filename)
        experiment_names = None
        try:
            experiment_names = simplejson.load(fp)
        except Exception, e:
            l.error("Unable to parse experiment file %s: %s" % (filename, e))
            raise e
        finally:
            fp.close()
        
        for entry in experiment_names:
            for key in entry.keys():
                if key not in ExperimentLoader.ALLOWED_ATTRIBUTES:
                    l.warning("Ignoring unrecognized key %s on experiment "
                              "definition %s in filename %s" %
                              (key, entry, filename))
            if ExperimentLoader.NAME_ATTRIBUTE in entry:
                Experiment.objects.get_or_create(
                    name=entry.get(ExperimentLoader.NAME_ATTRIBUTE))
            else:
                l.warning("Invalid entry in experiment file %s : %s" %
                    (filename, entry))
    
