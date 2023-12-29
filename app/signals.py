# signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.apps import apps
from api.ws_actions import send_channel_message

# not needed right now...
# @receiver(post_save, sender=apps.get_model('app', 'CompetitionLog'))
# def handle_model_creation(sender, instance, created, **kwargs):
#     if created:
#         send_channel_message(instance.competition.name, "eventUpdated", instance.label)
