# Generated by Django 3.2.6 on 2022-01-24 14:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('paster', '0015_auto_20220122_0059'),
    ]

    operations = [
        migrations.AddField(
            model_name='paste',
            name='link_self',
            field=models.CharField(blank=True, max_length=150, null=True, verbose_name='Ссылка на пасту (в пастере)'),
        ),
    ]
