# Generated by Django 2.1.3 on 2018-12-06 11:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('webtech', '0012_event_datetime'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='name',
            field=models.CharField(max_length=100),
        ),
    ]