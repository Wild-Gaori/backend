from rest_framework import serializers

class ImageGenerationSerializer(serializers.Serializer):
    prompt = serializers.CharField(required=True, max_length=255)
