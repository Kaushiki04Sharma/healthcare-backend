from rest_framework import serializers

from doctors.models import Doctor
from doctors.serializers import DoctorSerializer
from patients.models import Patient

from .models import PatientDoctorMapping


class MappingSerializer(serializers.ModelSerializer):
    patient = serializers.PrimaryKeyRelatedField(queryset=Patient.objects.all())
    doctor = serializers.PrimaryKeyRelatedField(queryset=Doctor.objects.all())
    patient_name = serializers.CharField(source="patient.name", read_only=True)
    doctor_name = serializers.CharField(source="doctor.name", read_only=True)

    class Meta:
        model = PatientDoctorMapping
        fields = ("id", "patient", "patient_name", "doctor", "doctor_name", "created_at")
        read_only_fields = ("id", "created_at")

    def validate_patient(self, patient):
        request = self.context["request"]
        # Users may only assign doctors to patients they created.
        if patient.created_by_id != request.user.id:
            raise serializers.ValidationError("Patient not found.")
        return patient

    def validate(self, attrs):
        if PatientDoctorMapping.objects.filter(
            patient=attrs["patient"], doctor=attrs["doctor"]
        ).exists():
            raise serializers.ValidationError("This doctor is already assigned to this patient.")
        return attrs


class PatientDoctorSerializer(serializers.ModelSerializer):
    """Used by GET /api/mappings/<patient_id>/ : a mapping with full doctor details."""

    mapping_id = serializers.IntegerField(source="id", read_only=True)
    doctor = DoctorSerializer(read_only=True)

    class Meta:
        model = PatientDoctorMapping
        fields = ("mapping_id", "doctor", "created_at")
