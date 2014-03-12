# -*- coding: utf-8 -*-
from __future__ import absolute_import

import logging
l = logging.getLogger(__name__)

from django import template

from django_lean.experiments.models import Experiment
from django_lean.experiments.utils import WebUserFactory


register = template.Library()

class BaseExperimentNode(template.Node):
    def __init__(self, user_factory=WebUserFactory()):
        self.__user_factory = user_factory
    
    def create_user(self, context):
        return self.__user_factory.create_user(context)

    def get_user(self, context):
        request = context.get('request', None)
        if request is None:
            return self.create_user(context)
        if not hasattr(request, 'experiment_user'):
            request.experiment_user = self.create_user(context)
        return request.experiment_user


class ExperimentNode(BaseExperimentNode):
    def __init__(self, node_list, experiment_name, group_name, user_factory):
        BaseExperimentNode.__init__(self, user_factory)
        self.node_list = node_list
        self.experiment_name = experiment_name
        self.group_name = group_name

    def render(self, context):
        user = self.get_user(context)
        should_render = False
        
        if self.group_name == "test":
            should_render = Experiment.test(self.experiment_name, user)
        elif self.group_name == "control":
            should_render = Experiment.control(self.experiment_name, user)
        else:
            raise Exception("Unknown Experiment group name : %s" %
                            self.group_name)
        
        if should_render:
            return self.node_list.render(context)
        else:
            return ""
    

@register.tag('experiment')
def experiment(parser, token, user_factory=WebUserFactory()):
    """
    Split Testing experiment tag has the following syntax :
    
    {% experiment <experiment_name> <group_name>  %}
    experiment content goes here
    {% endexperiment %}
    
    If the group name is neither 'test' nor 'control' an exception is raised
    during rendering.
    """
    try:
        tag_name, experiment_name, group_name = token.split_contents()
        node_list = parser.parse(('endexperiment', ))
        parser.delete_first_token()
    except ValueError:
        raise template.TemplateSyntaxError("Syntax should be like :"
                "{% experiment experiment_name group_name  %}")
    
    return ExperimentNode(node_list, experiment_name, group_name, user_factory)

class ClientSideExperimentNode(BaseExperimentNode):
    CONTEXT_KEY = "client_side_experiments"
    
    def __init__(self, experiment_name, user_factory):
        BaseExperimentNode.__init__(self, user_factory)
        self.experiment_name = experiment_name
    
    def render(self, context):
        """
        Appends to a 'client_side_experiments' variable in the context. It
        will be the templates responsibility to render this list into the
        Javascript context.
        """
        if self.CONTEXT_KEY not in context:
            context[self.CONTEXT_KEY]= {}
        
        if self.experiment_name not in context[self.CONTEXT_KEY]:
            user = self.create_user(context)
            group = None
            
            if Experiment.test(self.experiment_name, user):
                group = "test"
            elif Experiment.control(self.experiment_name, user):
                group = "control"
            else:
                raise Exception("Unexpected test group for experiment %s" %
                                self.experiment_name)
            
            context[self.CONTEXT_KEY][self.experiment_name] = group
        return ""
    

@register.tag('clientsideexperiment')
def clientsideexperiment(parser, token, user_factory=WebUserFactory()):
    """
    Used to declare an experiment that affects JavaScript :
    
    (in template)
    {% clientsideexperiment <experiment_name> %}
    
    (in Javascript)
    if (experiment.test("<experiment_name>")) {
      // test case
    } else {
      // control case
    }
    
    The template tag populates the context with a dict at
    'client_side_experiments' with entries for each experiment name that map to
    either 'test' or 'control'.
    """
    try:
        tag_name, experiment_name = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError("Syntax should be like :"
                "{% clientsideexperiment experiment_name  %}")
    
    return ClientSideExperimentNode(experiment_name, user_factory)
