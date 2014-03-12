# -*- coding: utf-8 -*-
import os

from django_lean.experiments.loader import ExperimentLoader
from django_lean.experiments.models import Experiment
from django_lean.experiments.tests.utils import TestCase


def get_experiments(filename):
    dirname = os.path.dirname(__file__) or os.path.curdir
    return os.path.join(dirname, "data", filename)


class TestExperimentLoader(TestCase):
    def testInvalidExperimentDefinition(self):
        filename = get_experiments("test_invalid_experiments.json")
        ExperimentLoader.load_experiments(filename)
    
    def testMissingExperimentDefinition(self):
        filename = get_experiments("non_existant_file.json")
        self.assertRaises(Exception, lambda: ExperimentLoader.load_experiments(filename))
    
    def testExperimentLoader(self):
        filename1 = get_experiments("test_experiments.json")
        filename2 = get_experiments("test_experiments2.json")
        
        count = Experiment.objects.all().count()
        
        ExperimentLoader.load_experiments(filename1)
        
        new_count = Experiment.objects.all().count()
        self.assertEquals(count+3, new_count)
        
        experiment1 = Experiment.objects.get(name="Test Experiment #1")
        experiment2 = Experiment.objects.get(name="Test Experiment #2")
        experiment3 = Experiment.objects.get(name="Test Experiment #3")
        self.assertEquals(0, Experiment.objects.filter(
                          name="Test Experiment #4").count())
        
        self.assertEquals(experiment1.state, Experiment.DISABLED_STATE)
        self.assertEquals(experiment1.start_date, None)
        self.assertEquals(experiment1.end_date, None)
        
        experiment1.state = Experiment.ENABLED_STATE
        experiment1.save()
        
        self.assertNotEquals(experiment1.start_date, None)
        
        ExperimentLoader.load_experiments(filename1)
        
        # assert no new experiments loaded
        new_count = Experiment.objects.all().count()
        self.assertEquals(count+3, new_count)
        
        # make sure that experiment1 is still enabled
        experiment1 = Experiment.objects.get(name="Test Experiment #1")
        self.assertEquals(experiment1.state, Experiment.ENABLED_STATE)
        self.assertNotEquals(experiment1.start_date, None)
        self.assertEquals(experiment1.end_date, None)
        
        ExperimentLoader.load_experiments(filename2)
        # assert 1 new experiment loaded
        new_count = Experiment.objects.all().count()
        self.assertEquals(count+4, new_count)
        experiment4 = Experiment.objects.get(name="Test Experiment #4")
    
