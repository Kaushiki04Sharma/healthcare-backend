from rest_framework import serializers

from .models import Patient


class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = (
            "id",
            "name",
            "age",
            "gender",
            "phone",
            "address",
            "medical_history",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Name cannot be blank.")
        return value

    def validate_age(self, value):
        if value > 150:
            raise serializers.ValidationError("Age must be 150 or less.")
        return value

    def validate_phone(self, value):
        if value and not value.replace("+", "").replace("-", "").replace(" ", "").isdigit():
            raise serializers.ValidationError("Phone may contain only digits, spaces, '+' and '-'.")
        return value
