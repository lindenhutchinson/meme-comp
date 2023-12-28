from rest_framework import serializers
from app.models import Meme


class MemeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Meme
        fields = ("id", "participant", "competition")
