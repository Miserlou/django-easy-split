# -*- coding: utf-8 -*-
from south.db import db

from django.db import models

from django_lean.experiments.models import *

class Migration:
    def forwards(self, orm):
        # Adding model 'DailyConversionReport'
        db.create_table('experiments_dailyconversionreport', (
            ('id', orm['experiments.dailyconversionreport:id']),
            ('date', orm['experiments.dailyconversionreport:date']),
            ('experiment', orm['experiments.dailyconversionreport:experiment']),
            ('overall_test_conversion', orm['experiments.dailyconversionreport:overall_test_conversion']),
            ('overall_control_conversion', orm['experiments.dailyconversionreport:overall_control_conversion']),
            ('test_group_size', orm['experiments.dailyconversionreport:test_group_size']),
            ('control_group_size', orm['experiments.dailyconversionreport:control_group_size']),
            ('confidence', orm['experiments.dailyconversionreport:confidence']),
        ))
        db.send_create_signal('experiments', ['DailyConversionReport'])
        
        # Adding model 'DailyConversionReportGoalData'
        db.create_table('experiments_dailyconversionreportgoaldata', (
            ('id', orm['experiments.dailyconversionreportgoaldata:id']),
            ('report', orm['experiments.dailyconversionreportgoaldata:report']),
            ('goal_type', orm['experiments.dailyconversionreportgoaldata:goal_type']),
            ('test_conversion', orm['experiments.dailyconversionreportgoaldata:test_conversion']),
            ('control_conversion', orm['experiments.dailyconversionreportgoaldata:control_conversion']),
            ('confidence', orm['experiments.dailyconversionreportgoaldata:confidence']),
        ))
        db.send_create_signal('experiments', ['DailyConversionReportGoalData'])
    
    def backwards(self, orm):    
        # Deleting model 'DailyConversionReport'
        db.delete_table('experiments_dailyconversionreport')
        
        # Deleting model 'DailyConversionReportGoalData'
        db.delete_table('experiments_dailyconversionreportgoaldata')
    
    models = {
        'auth.group': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '80', 'unique': 'True'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'unique_together': "(('content_type', 'codename'),)"},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '30', 'unique': 'True'})
        },
        'contenttypes.contenttype': {
            'Meta': {'unique_together': "(('app_label', 'model'),)", 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'experiments.anonymousvisitor': {
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'experiments.dailyactivityreport': {
            'confidence': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'control_group_size': ('django.db.models.fields.IntegerField', [], {}),
            'control_score': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'date': ('django.db.models.fields.DateField', [], {}),
            'experiment': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['experiments.Experiment']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'test_group_size': ('django.db.models.fields.IntegerField', [], {}),
            'test_score': ('django.db.models.fields.FloatField', [], {'null': 'True'})
        },
        'experiments.dailyconversionreport': {
            'confidence': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'control_group_size': ('django.db.models.fields.IntegerField', [], {}),
            'date': ('django.db.models.fields.DateField', [], {}),
            'experiment': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['experiments.Experiment']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'overall_control_conversion': ('django.db.models.fields.IntegerField', [], {}),
            'overall_test_conversion': ('django.db.models.fields.IntegerField', [], {}),
            'test_group_size': ('django.db.models.fields.IntegerField', [], {})
        },
        'experiments.dailyconversionreportgoaldata': {
            'confidence': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'control_conversion': ('django.db.models.fields.IntegerField', [], {}),
            'goal_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['experiments.GoalType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'report': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['experiments.DailyConversionReport']"}),
            'test_conversion': ('django.db.models.fields.IntegerField', [], {})
        },
        'experiments.experiment': {
            'end_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128', 'unique': 'True'}),
            'start_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'state': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'experiments.goalrecord': {
            'anonymous_visitor': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['experiments.AnonymousVisitor']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'goal_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['experiments.GoalType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'experiments.goaltype': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128', 'unique': 'True'})
        },
        'experiments.participant': {
            'Meta': {'unique_together': "(('user', 'experiment'), ('anonymous_visitor', 'experiment'))"},
            'anonymous_visitor': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['experiments.AnonymousVisitor']", 'null': 'True', 'blank': 'True'}),
            'enrollment_date': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'experiment': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['experiments.Experiment']"}),
            'group': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True'})
        }
    }
    
    complete_apps = ['experiments']
