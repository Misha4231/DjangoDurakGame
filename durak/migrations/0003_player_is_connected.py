# Generated by Django 5.1.5 on 2025-02-16 08:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('durak', '0002_room_game_state'),
    ]

    operations = [
        migrations.AddField(
            model_name='player',
            name='is_connected',
            field=models.BooleanField(default=False),
        ),
    ]
