from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from .models import Doctor
from .permissions import IsCreatorOrReadOnly
from .serializers import DoctorSerializer


class DoctorListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/doctors/  -> all doctors
    POST /api/doctors/  -> add a doctor
    """

    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class DoctorDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET / PUT / PATCH / DELETE /api/doctors/<id>/
    Everyone authenticated can read; only the creator can update or delete.
    """

    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer
    permission_classes = [IsAuthenticated, IsCreatorOrReadOnly]
