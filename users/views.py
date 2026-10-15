from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken

from .models import UserProfile
from .serializers import (
    RegisterSerializer, LoginSerializer, UserSerializer,
    PasswordChangeSerializer
)



class RegisterView(generics.CreateAPIView):
    """POST /api/v1/auth/register/ — create account + auto-profile + return JWT."""
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """POST /api/v1/auth/login/ — authenticate and return JWT pair."""
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username_or_email = serializer.validated_data['username']
        user = authenticate(
            username=username_or_email,
            password=serializer.validated_data['password'],
        )
        if not user and '@' in username_or_email:
            try:
                matched_user = User.objects.get(email__iexact=username_or_email)
                user = authenticate(
                    username=matched_user.username,
                    password=serializer.validated_data['password'],
                )
            except (User.DoesNotExist, User.MultipleObjectsReturned):
                user = None
        if not user:
            return Response({'detail': 'Invalid credentials.'}, status=status.HTTP_401_UNAUTHORIZED)
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        })


class LogoutView(APIView):
    """POST /api/v1/auth/logout/ — blacklist refresh token."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception:
            pass
        return Response({'detail': 'Logged out.'}, status=status.HTTP_205_RESET_CONTENT)


class ProfileView(generics.RetrieveUpdateAPIView):
    """GET/PUT /api/v1/users/profile/ — retrieve or update own profile."""
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class PasswordChangeView(APIView):
    """POST /api/v1/auth/password/change/ — change user password."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        if not user.check_password(serializer.validated_data['old_password']):
            return Response({'old_password': ['Incorrect current password.']}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({'detail': 'Password changed successfully.'}, status=status.HTTP_200_OK)
from .services import UserPreferencesService


class UserPreferencesView(APIView):
    """GET/POST /api/v1/users/preferences/ — retrieve or update user fitness preferences."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        prefs = UserPreferencesService.get_user_preferences(request.user)
        return Response(prefs, status=status.HTTP_200_OK)

    def post(self, request):
        unit_system = request.data.get('unit_system', 'metric')
        target_workouts = request.data.get('target_weekly_workouts')
        if target_workouts is not None:
            try:
                target_workouts = int(target_workouts)
                if 1 <= target_workouts <= 7:
                    profile, _ = UserProfile.objects.get_or_create(user=request.user)
                    profile.weekly_workouts_target = target_workouts
                    profile.save(update_fields=['weekly_workouts_target'])
            except (ValueError, TypeError):
                return Response({'detail': 'Invalid target_weekly_workouts value.'}, status=status.HTTP_400_BAD_REQUEST)

        prefs = UserPreferencesService.get_user_preferences(request.user)
        prefs['unit_system'] = unit_system
        if unit_system == 'imperial':
            prefs['weight_unit'] = 'lbs'
            prefs['distance_unit'] = 'miles'
        return Response(prefs, status=status.HTTP_200_OK)
