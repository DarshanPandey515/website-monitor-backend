from rest_framework import serializers
from .models import *


class WebsiteSerializer(serializers.ModelSerializer):

    class Meta:
        model = Website
        fields = [
            "id",
            "website_name",
            "website_url",
            "interval",
            "last_checked",
            "last_status",
            "last_response_time",
        ]

    def validate_interval(self, value):
        if value < 1 or value > 1440:
            raise serializers.ValidationError(
                "Interval must be between 1 and 1440 minutes")
        return value


class CheckResultSerializer(serializers.ModelSerializer):

    class Meta:
        model = CheckResult
        fields = [
            "id",
            "checked_at",
            "status",
            "status_code",
            "response_time",
            "error_message",
        ]
