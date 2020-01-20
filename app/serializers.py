from rest_framework import serializers


class SessionSerializer(serializers.Serializer):
    client_initial = serializers.CharField(max_length=10)
    client_name = serializers.CharField(max_length=200)
    duration = serializers.CharField(max_length=50)
    date = serializers.DateField()
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()
    type = serializers.CharField(max_length=200)
    notes = serializers.CharField()
    updated_at = serializers.CharField(max_length=50)
    status = serializers.CharField(max_length=20, default='NEW')
    is_accepted = serializers.BooleanField()
