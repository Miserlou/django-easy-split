from django.dispatch import Signal


goal_recorded = Signal(providing_args=['goal_record', 'experiment_user'])

user_enrolled = Signal(providing_args=['experiment', 'experiment_user',
                                       'group_id'])
