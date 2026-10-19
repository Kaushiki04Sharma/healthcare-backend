from rest_framework import serializers

from .models import Doctor


class DoctorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Doctor
        fields = (
            "id",
            "name",
            "specialization",
            "email",
            "phone",
            "experience_years",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Name cannot be blank.")
        return value

    def validate_email(self, value):
        value = value.strip().lower()
        qs = Doctor.objects.filter(email__iexact=value)
        if self.instance is not None:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("A doctor with this email already exists.")
        return value

    def validate_experience_years(self, value):
        if value > 80:
            raise serializers.ValidationError("Experience must be 80 years or less.")
        return value
