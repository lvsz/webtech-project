# Generated by Django 2.1.2 on 2018-12-15 18:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('webtech', '0027_auto_20181215_1805'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='image',
            field=models.ImageField(default='default.png', upload_to='images'),
        ),
        migrations.AlterField(
            model_name='venue',
            name='image',
            field=models.ImageField(default='default.png', upload_to='images'),
        ),
    ]
