"""Standalone views for accounts."""
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from accounts.permissions import IsGerant
from accounts.serializers import (
    MonexaTokenObtainPairSerializer,
    OrganizationSerializer,
    RegisterSerializer,
    UserSerializer,
)


class MonexaTokenObtainPairView(TokenObtainPairView):
    serializer_class = MonexaTokenObtainPairSerializer


class Toggle2FAView(APIView):
    """PATCH /api/auth/me/2fa/ — toggle 2FA for the GERANT only."""
    permission_classes = [IsAuthenticated, IsGerant]

    def patch(self, request):
        user = request.user
        user.is_2fa_enabled = not user.is_2fa_enabled
        user.save(update_fields=["is_2fa_enabled"])
        return Response({"is_2fa_enabled": user.is_2fa_enabled})


class RegisterView(APIView):
    """POST /api/auth/register/ — crée l'organisation + le gérant fondateur."""
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "user": UserSerializer(user).data,
                "organization": OrganizationSerializer(user.organization).data,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_201_CREATED,
        )


class OrganizationMeView(APIView):
    """GET/PATCH /api/organizations/me/ — fiche entreprise du locataire courant."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        org = request.user.organization
        if org is None:
            return Response(
                {"error": {"code": "NO_ORGANIZATION", "message": "Aucune organisation rattachée."}},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(OrganizationSerializer(org).data)

    def patch(self, request):
        if not request.user.is_gerant():
            return Response(
                {"error": {"code": "FORBIDDEN", "message": "Seul le gérant peut modifier l'entreprise."}},
                status=status.HTTP_403_FORBIDDEN,
            )
        org = request.user.organization
        if org is None:
            return Response(
                {"error": {"code": "NO_ORGANIZATION", "message": "Aucune organisation rattachée."}},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = OrganizationSerializer(org, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
