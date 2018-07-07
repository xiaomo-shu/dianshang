from rest_framework import serializers
from .models import Area


class AreasSerializer(serializers.ModelSerializer):
    class Meta:
        model = Area
        fields = ('id', 'name')


class SubAreasSerializer(serializers.ModelSerializer):
    subs = AreasSerializer(many=True)

    class Meta:
        model = Area
        fields = ('id', 'name', 'subs')