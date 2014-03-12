# -*- coding: utf-8 -*-
from django.contrib import admin

from django_lean.experiments.models import (Experiment, Participant,
                                            GoalType, AnonymousVisitor)


class GoalTypeOptions(admin.ModelAdmin):
    list_display = ('name',)

class ExperimentOptions(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'state')
    list_filter = ('name', )
    search_fields = ('name', )

class ParticipantOptions(admin.ModelAdmin):
    list_display = ('user', 'experiment', 'group')
    list_filter = ('group',)
    search_fields = ('user',)
    raw_id_fields = ('user', 'anonymous_visitor')

admin.site.register(AnonymousVisitor)
admin.site.register(GoalType, GoalTypeOptions)
admin.site.register(Experiment, ExperimentOptions)
admin.site.register(Participant, ParticipantOptions)
