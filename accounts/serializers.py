from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers


class RegisterSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8, style={"input_type": "password"})

    def validate_email(self, value):
        value = value.strip().lower()
        if User.objects.filter(username__iexact=value).exists() or User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate(self, attrs):
        # Run Django's password validators (common passwords, similarity, etc.)
        temp_user = User(username=attrs["email"], email=attrs["email"], first_name=attrs["name"])
        try:
            validate_password(attrs["password"], user=temp_user)
        except Exception as exc:  # DjangoValidationError
            messages = getattr(exc, "messages", [str(exc)])
            raise serializers.ValidationError({"password": messages})
        return attrs

    def create(self, validated_data):
        # The email is used as the username so users log in with email + password.
        return User.objects.create_user(
            username=validated_data["email"],
            email=validated_data["email"],
            first_name=validated_data["name"],
            password=validated_data["password"],
        )


class UserSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="first_name", read_only=True)

    class Meta:
        model = User
        fields = ("id", "name", "email")


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate(self, attrs):
        email = attrs["email"].strip().lower()
        user = authenticate(
            request=self.context.get("request"),
            username=email,
            password=attrs["password"],
        )
        if user is None:
            raise serializers.ValidationError("Invalid email or password.")
        if not user.is_active:
            raise serializers.ValidationError("This account is disabled.")
        attrs["user"] = user
        return attrs
