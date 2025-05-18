from rest_framework import serializers
from .models import EmailTemplate, SentEmail
from contacts.serializers import ContactSerializer

class EmailTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailTemplate
        fields = ['id', 'name', 'subject', 'body', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def create(self, validated_data):
        # Set the user from the request
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

class SentEmailSerializer(serializers.ModelSerializer):
    contact = ContactSerializer(read_only=True)
    template_name = serializers.SerializerMethodField()
    
    class Meta:
        model = SentEmail
        fields = ['id', 'contact', 'template', 'template_name', 'subject', 'body', 
                  'sent_at', 'scheduled_time', 'opened', 'opened_at', 'clicked', 'clicked_at']
        read_only_fields = ['id', 'sent_at', 'scheduled_time', 'opened', 'opened_at', 'clicked', 'clicked_at']
    
    def get_template_name(self, obj):
        if obj.template:
            return obj.template.name
        return None 