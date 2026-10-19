from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from .models import Patient
from .serializers import PatientSerializer


class PatientListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/patients/  -> patients created by the authenticated user
    POST /api/patients/  -> create a patient owned by the authenticated user
    """

    serializer_class = PatientSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Patient.objects.filter(created_by=self.request.user)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class PatientDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET / PUT / PATCH / DELETE /api/patients/<id>/
    Only the user who created the patient can access it (others get 404).
    """

    serializer_class = PatientSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Patient.objects.filter(created_by=self.request.user)
