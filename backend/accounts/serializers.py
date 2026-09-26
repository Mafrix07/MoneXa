"""Serializers for the accounts app."""
from django.utils import timezone
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .bootstrap import get_or_create_organization
from .models import Organization, User, Role


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = [
            "id", "name", "slug", "sector", "country", "currency",
            "legal_id", "onboarded_at", "created_at",
        ]
        read_only_fields = ["id", "slug", "onboarded_at", "created_at"]


class MonexaTokenObtainPairSerializer(TokenObtainPairSerializer):
    """JWT login with email + user payload so the client need not call /me immediately."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role
        token["email"] = user.email
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data


class UserSerializer(serializers.ModelSerializer):
    display_name = serializers.CharField(read_only=True)
    organization_name = serializers.CharField(source="organization.name", read_only=True, default="")
    password = serializers.CharField(write_only=True, required=False, style={"input_type": "password"})

    class Meta:
        model = User
        fields = [
            "id", "email", "username", "display_name", "role", "phone",
            "organization", "organization_name",
            "is_2fa_enabled", "is_staff", "is_active", "date_joined", "password",
        ]
        read_only_fields = ["id", "date_joined", "is_staff", "display_name", "organization"]

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for k, v in validated_data.items():
            setattr(instance, k, v)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={"input_type": "password"})
    password2 = serializers.CharField(write_only=True, required=True, style={"input_type": "password"})
    organization_name = serializers.CharField(write_only=True, max_length=200)
    sector = serializers.CharField(write_only=True, required=False, allow_blank=True, default="")
    country = serializers.CharField(write_only=True, required=False, default="TG", max_length=2)
    currency = serializers.CharField(write_only=True, required=False, default="XOF", max_length=3)
    legal_id = serializers.CharField(write_only=True, required=False, allow_blank=True, default="")

    class Meta:
        model = User
        fields = [
            "email", "phone", "password", "password2",
            "organization_name", "sector", "country", "currency", "legal_id",
        ]

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError({"password": "Les mots de passe ne correspondent pas."})
        return attrs

    def create(self, validated_data):
        validated_data.pop("password2")
        password = validated_data.pop("password")
        org_name = validated_data.pop("organization_name")
        sector = validated_data.pop("sector", "")
        country = validated_data.pop("country", "TG")
        currency = validated_data.pop("currency", "XOF")
        legal_id = validated_data.pop("legal_id", "")
        org = get_or_create_organization(
            name=org_name,
            sector=sector,
            country=country or "TG",
            currency=currency or "XOF",
            legal_id=legal_id or "",
        )
        if org.onboarded_at is None:
            org.onboarded_at = timezone.now()
            org.save(update_fields=["onboarded_at"])
        user = User(
            email=validated_data["email"],
            phone=validated_data.get("phone", ""),
            role=Role.GERANT,
            organization=org,
        )
        user.set_password(password)
        user.save()
        return user
