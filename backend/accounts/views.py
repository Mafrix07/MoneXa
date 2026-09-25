"""Standalone views for accounts."""
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsGerant


class Toggle2FAView(APIView):
    """PATCH /api/auth/me/2fa/ — toggle 2FA for the GERANT only."""
    permission_classes = [IsAuthenticated, IsGerant]

    def patch(self, request):
        user = request.user
        user.is_2fa_enabled = not user.is_2fa_enabled
        user.save(update_fields=["is_2fa_enabled"])
        return Response({"is_2fa_enabled": user.is_2fa_enabled})
