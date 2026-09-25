"""Assistant serializers."""
from rest_framework import serializers


class AskSerializer(serializers.Serializer):
    question = serializers.CharField(
        min_length=3, max_length=500,
        help_text="Question en langage naturel (FR/Ewé/Kabyé).",
    )


class AnswerSerializer(serializers.Serializer):
    answer = serializers.CharField()
    question = serializers.CharField()
