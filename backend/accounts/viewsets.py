"""Viewsets for accounts — Me + User CRUD (admin only)."""
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import User
from .permissions import IsGerant
from .serializers import UserSerializer


class MeViewSet(viewsets.GenericViewSet):
    """GET /api/auth/me/ — current user profile."""
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def retrieve(self, request, *args, **kwargs):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


class UserViewSet(viewsets.ModelViewSet):
    """User management — GERANT only."""
    queryset = User.objects.all().order_by("-date_joined")
    serializer_class = UserSerializer
    permission_classes = [IsGerant]
    filterset_fields = ["role", "is_active"]
    search_fields = ["email", "phone"]
    ordering_fields = ["date_joined", "email"]
