# Generated by Django 5.1.1 on 2024-11-05 00:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='selected_docent_id',
            field=models.IntegerField(default=1),
        ),
    ]
