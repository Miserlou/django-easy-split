# -*- coding: utf-8 -*-
from south.db import db

from django.db import models

from django_lean.experiments.models import *

class Migration:
    def forwards(self, orm):
        # Adding model 'Experiment'
        db.create_table('experiments_experiment', (
            ('id', orm['experiments.Experiment:id']),
            ('name', orm['experiments.Experiment:name']),
            ('state', orm['experiments.Experiment:state']),
            ('start_date', orm['experiments.Experiment:start_date']),
            ('end_date', orm['experiments.Experiment:end_date']),
        ))
        db.send_create_signal('experiments', ['Experiment'])
        
        # Adding model 'Participant'
        db.create_table('experiments_participant', (
            ('id', orm['experiments.Participant:id']),
            ('user', orm['experiments.Participant:user']),
            ('experiment', orm['experiments.Participant:experiment']),
            ('enrollment_date', orm['experiments.Participant:enrollment_date']),
            ('group', orm['experiments.Participant:group']),
        ))
        db.send_create_signal('experiments', ['Participant'])
        
        # Adding model 'DailyReport'
        db.create_table('experiments_dailyreport', (
            ('id', orm['experiments.DailyReport:id']),
            ('date', orm['experiments.DailyReport:date']),
            ('experiment', orm['experiments.DailyReport:experiment']),
            ('test_score', orm['experiments.DailyReport:test_score']),
            ('control_score', orm['experiments.DailyReport:control_score']),
        ))
        db.send_create_signal('experiments', ['DailyReport'])
        
        # Creating unique_together for [user, experiment] on Participant.
        db.create_unique('experiments_participant', ['user_id', 'experiment_id'])
    
    def backwards(self, orm):    
        # Deleting model 'Experiment'
        db.delete_table('experiments_experiment')
        
        # Deleting model 'Participant'
        db.delete_table('experiments_participant')
        
        # Deleting model 'DailyReport'
        db.delete_table('experiments_dailyreport')
        
        # Deleting unique_together for [user, experiment] on Participant.
        db.delete_unique('experiments_participant', ['user_id', 'experiment_id'])
    

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
        'experiments.dailyreport': {
            'control_score': ('django.db.models.fields.FloatField', [], {}),
            'date': ('django.db.models.fields.DateField', [], {}),
            'experiment': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['experiments.Experiment']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'test_score': ('django.db.models.fields.FloatField', [], {})
        },
        'experiments.experiment': {
            'end_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128', 'unique': 'True'}),
            'start_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'state': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'experiments.participant': {
            'Meta': {'unique_together': "(('user', 'experiment'),)"},
            'enrollment_date': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'experiment': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['experiments.Experiment']"}),
            'group': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        }
    }
    
    complete_apps = ['experiments']
