from rest_framework import serializers
from .models import Activity
from django.contrib.auth.models import User

class UserMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']

class ActivitySerializer(serializers.ModelSerializer):
    user = UserMinimalSerializer(read_only=True)
    
    class Meta:
        model = Activity
        fields = ['id', 'user', 'activity_type', 'description', 'timestamp']
        read_only_fields = ['id', 'timestamp'] 