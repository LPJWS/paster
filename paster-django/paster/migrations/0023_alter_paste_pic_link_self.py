# Generated by Django 3.2.6 on 2024-07-10 14:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('paster', '0022_pastesuggest'),
    ]

    operations = [
        migrations.AlterField(
            model_name='paste',
            name='pic_link_self',
            field=models.CharField(blank=True, max_length=500, null=True, verbose_name='Ссылка на картинку'),
        ),
    ]
