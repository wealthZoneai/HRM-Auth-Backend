# login/serializers.py
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import PasswordResetOTP
from .utils import generate_otp, send_otp_email

User = get_user_model()


class CustomTokenSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role
        token["username"] = user.username
        token["email"] = user.email
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data["role"] = self.user.role
        data["username"] = self.user.username

        role_redirects = {
            "management": "/dashboard/management",
            "hr": "/dashboard/hr",
            "tl": "/dashboard/tl",
            "employee": "/dashboard/employee",
            "intern": "/dashboard/intern",
        }

        data["redirect_url"] = role_redirects.get(self.user.role, "/")
        return data


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        email = value.lower()
        return email

    def create(self, validated_data):
        email = validated_data["email"]
        user = User.objects.filter(email=email).first()

        if not user:
            raise serializers.ValidationError({"email": "Email not found."})

        otp = generate_otp()
        PasswordResetOTP.objects.create(user=user, otp=otp)
        send_otp_email(email, otp)

        # Return an object that contains at least the serializer fields (here: email).
        # The view expects serializer.data to be usable, so include 'email' in returned dict.
        return {"email": email}


class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=4)

    def validate(self, data):
        email = data["email"]
        otp = data["otp"]

        user = User.objects.filter(email=email).first()
        if not user:
            raise serializers.ValidationError({"email": "Email not found."})

        otp_obj = PasswordResetOTP.objects.filter(
            user=user, otp=otp, is_used=False
        ).last()

        if not otp_obj:
            raise serializers.ValidationError({"otp": "Invalid OTP."})

        if otp_obj.is_expired():
            raise serializers.ValidationError({"otp": "OTP expired."})

        data["user"] = user
        data["otp_obj"] = otp_obj
        return data

    def create(self, validated_data):
        email = validated_data["email"]
        otp = validated_data["otp"]

        otp_obj = PasswordResetOTP.objects.filter(user__email=email).latest('id')

        if otp_obj.otp != otp:
            raise serializers.ValidationError({"otp": "Invalid OTP"})

    # Return value must include all serializer fields (email, otp)
        return {
            "email": email,
            "otp": otp
        }



class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        if data["new_password"] != data["confirm_password"]:
            raise serializers.ValidationError(
                {"confirm_password": "Passwords do not match"}
            )

        pwd = data["new_password"]

        if len(pwd) < 8:
            raise serializers.ValidationError(
                {"new_password": "Min 8 characters"})
        if not any(c.isdigit() for c in pwd):
            raise serializers.ValidationError(
                {"new_password": "Must include a number"})
        if not any(c.isupper() for c in pwd):
            raise serializers.ValidationError(
                {"new_password": "Must include uppercase"})
        if not any(c.islower() for c in pwd):
            raise serializers.ValidationError(
                {"new_password": "Must include lowercase"})
        if not any(c in "!@#$%^&*()_+{}[]|:;'<>,.?/" for c in pwd):
            raise serializers.ValidationError(
                {"new_password": "Must include special"})

        return data

    def create(self, validated_data):
        user = User.objects.filter(email=validated_data["email"]).first()
        if not user:
            raise serializers.ValidationError({"email": "Email not found."})

        user.set_password(validated_data["new_password"])
        user.save()

        return {
            "email": validated_data["email"]
        }
