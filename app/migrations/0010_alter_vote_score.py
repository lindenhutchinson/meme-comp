# Generated by Django 4.2.1 on 2023-08-04 09:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0009_competition_winning_meme_alter_meme_user_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='vote',
            name='score',
            field=models.FloatField(),
        ),
    ]
