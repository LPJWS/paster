# Generated by Django 3.2.6 on 2021-09-30 13:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('paster', '0007_alter_mark_member'),
    ]

    operations = [
        migrations.AddField(
            model_name='mark',
            name='created_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
