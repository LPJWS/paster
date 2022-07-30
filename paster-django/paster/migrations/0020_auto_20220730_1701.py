# Generated by Django 3.2.6 on 2022-07-30 14:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('paster', '0019_alter_paste_pic_link_self'),
    ]

    operations = [
        migrations.CreateModel(
            name='Chat',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('chat_id', models.IntegerField(unique=True, verbose_name='Chat id')),
                ('name', models.CharField(max_length=100, verbose_name='Имя чата')),
                ('messages_enabled', models.BooleanField(default=True, verbose_name='Разрешены сообщения?')),
            ],
            options={
                'verbose_name': 'Чат',
                'verbose_name_plural': 'Чаты',
            },
        ),
        migrations.AddIndex(
            model_name='chat',
            index=models.Index(fields=['chat_id'], name='paster_chat_chat_id_664f6c_idx'),
        ),
    ]
