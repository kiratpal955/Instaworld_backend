from django.contrib.auth import logout
from django.db.models import Q
from rest_framework import serializers, generics, viewsets, mixins, status, filters
from django.shortcuts import get_object_or_404
from rest_framework_simplejwt.authentication import JWTAuthentication

from rest_framework.authentication import BasicAuthentication
from rest_framework.mixins import CreateModelMixin, DestroyModelMixin, UpdateModelMixin, ListModelMixin
from rest_framework.permissions import IsAdminUser, AllowAny
from rest_framework.permissions import IsAuthenticated
from account.serializers import UserRegisterSerializer, UserLogInSerializer, UserChangePasswordSerializer, \
    DeleteUserSerializer, ProfileSerializer, UserSearchSerializer, FollowingSerializer, FollowersSerializer, \
    UserProfileOTPSerializer, ForgotPasswordOTPSerializer, ForgotPasswordSerializer, \
    UserProfileSerializer, UserFollowSerializer, UserSerializer, VerifyOTPSerializer, ProfileListSerializer
from post.utils import get_tokens_for_user
from django.contrib.auth.models import User
from rest_framework.viewsets import GenericViewSet

from .constants import absolute_url
from .models import UserProfile
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenRefreshView
from .serializers import TokenRefreshSerializer


class UserRegister(GenericViewSet, CreateModelMixin):
    """View to register user"""
    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer
    permission_classes = [AllowAny, ]
    http_method_names = ['post']

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        if serializer.is_valid(raise_exception=True):
            user, user_profile = serializer.create(serializer.validated_data)
            user_token = get_tokens_for_user(user)
            return Response({'token': user_token,
                             "message": "User created successfully",
                             "user_id": user.id,
                             "user_profile_id": user_profile.id},
                            status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserLogIn(GenericViewSet, CreateModelMixin):
    """View for login user"""
    queryset = User.objects.all()
    serializer_class = UserLogInSerializer
    http_method_names = ['post']

    def create(self, request, *args, **kwargs):

        data = request.data
        serializer = self.serializer_class(data=data)
        if serializer.is_valid():
            username_or_email = request.data.get('username')
            password = request.data.get('password')
            user = User.objects.filter(Q(email=username_or_email) | Q(username=username_or_email)).first()
            if not user:
                raise serializers.ValidationError("No such user found. Register First!")
            if user.check_password(password) and user.is_active:
                user_token = get_tokens_for_user(user)
                user_id = user.id

                return Response({'token': user_token,
                                 'user_id': user_id,
                                 "data": serializer.data,
                                 'message': "Successfully Logged In",
                                 }, status=status.HTTP_200_OK)
            elif not user.is_active:
                return Response({
                    'message': "Account is inactive",
                }, status=status.HTTP_401_UNAUTHORIZED)
        return Response({
            'error': "Invalid credentials"}, status=status.HTTP_404_NOT_FOUND)


class UserChangePassword(GenericViewSet, UpdateModelMixin):
    """View to change password of the user"""
    queryset = User
    serializer_class = UserChangePasswordSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self, queryset=None):
        queryset = self.request.user
        return queryset

    def update(self, request, *args, **kwargs):
        self.object = self.get_object()
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            if not self.object.check_password(serializer.data.get("password")):
                return Response({"password": "Wrong password."}, status=status.HTTP_400_BAD_REQUEST)
            if request.data.get("new_password") != request.data.get("confirm_password"):
                return Response({"password": "Password and confirm password does not match!"},
                                status=status.HTTP_400_BAD_REQUEST)
            self.object.set_password(request.data.get("new_password"))
            self.object.save()
            response = {
                'status': 'success',
                'code': status.HTTP_200_OK,
                'message': 'Password updated successfully',
                'data': []
            }

            return Response(response)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteUser(GenericViewSet, DestroyModelMixin):
    """View for deleting user by admin user only"""
    queryset = User.objects.all()
    serializer_class = DeleteUserSerializer
    authentication_classes = [BasicAuthentication]
    permission_classes = [IsAdminUser]


class UserView(GenericViewSet, ListModelMixin, UpdateModelMixin):
    """View to get post of the users followed by user"""
    queryset = User
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = User.objects.filter(id=user.id)
        return queryset

    def update(self, request, *args, **kwargs):
        user = request.user
        serializer = UserSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class ProfileAPI(GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin, mixins.RetrieveModelMixin,
                 mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return UserProfile.objects.filter(user=user)
        else:
            return UserProfile.objects.none()


class FollowerViewSet(GenericViewSet, ListModelMixin):
    serializer_class = FollowersSerializer
    queryset = UserProfile.objects.all()
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'error': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)
        profile = UserProfile.objects.get(user=request.user)
        serializer = self.get_serializer(profile)
        return Response(serializer.data)


class FollowingViewSet(GenericViewSet, ListModelMixin):
    serializer_class = FollowingSerializer
    queryset = UserProfile.objects.all()
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        profile = UserProfile.objects.get(user=request.user)
        serializer = self.get_serializer(profile)
        return Response(serializer.data)


class VerifyOTPView(APIView):
    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user if request.user.is_authenticated else None)
            user = serializer.validated_data['user']
            if user:
                return Response({
                    'message': 'OTP verified successfully and account activated!'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'message': 'OTP verified successfully!'
                }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserSearchView(GenericViewSet):
    serializer_class = UserSearchSerializer

    # filter_backends = [filters.SearchFilter]
    # search_fields = ['^username', '^first_name', '^last_name']

    def list(self, request, *args, **kwargs):
        search = request.query_params.get('search')
        if search:
            queryset = User.objects.filter(Q(username__icontains=search) | Q(first_name__icontains=search) |
                                           Q(last_name__icontains=search))
        else:
            return Response({"message": "No user found"})
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class GenerateOTPView(generics.GenericAPIView, mixins.UpdateModelMixin):
    serializer_class = UserProfileOTPSerializer
    queryset = UserProfile.objects.all()

    def patch(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        user_profile = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        otp = serializer.generate_otp(user_profile, serializer.validated_data)
        user_profile_serializer = UserProfileOTPSerializer(user_profile)

        return Response({'message': 'OTP Sent successfully'},
                        status=status.HTTP_200_OK)


class UserFollowView(mixins.CreateModelMixin, GenericViewSet, mixins.DestroyModelMixin):
    serializer_class = UserFollowSerializer
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({'error': 'Please enter valid user id'}, status=status.HTTP_400_BAD_REQUEST)
        user_to_follow = get_object_or_404(User, id=user_id)
        if request.user == user_to_follow:
            return Response({'error': 'You cannot follow yourself'}, status=status.HTTP_400_BAD_REQUEST)

        if user_to_follow.userprofile.followers.filter(id=request.user.id).exists():
            user_to_follow.userprofile.followers.remove(request.user)
            return Response({'followed': False},
                            status=status.HTTP_200_OK)
        else:
            user_to_follow.userprofile.followers.add(request.user)
            serializer = self.get_serializer(request.user.userprofile)
            return Response({'followed': True,
                             'data': serializer.data}, status=status.HTTP_201_CREATED)


class ForgotPasswordOTPView(generics.GenericAPIView, mixins.UpdateModelMixin):
    serializer_class = ForgotPasswordOTPSerializer
    queryset = UserProfile.objects.all()

    def patch(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        user_profile = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        otp = serializer.generate_otp(user_profile, serializer.validated_data)
        user_profile_serializer = UserProfileOTPSerializer(user_profile)

        return Response(serializer.validated_data,
                        status=status.HTTP_200_OK)


class ForgotPassword(GenericViewSet, UpdateModelMixin):
    queryset = User.objects.all()
    serializer_class = ForgotPasswordSerializer

    def update(self, request, *args, **kwargs):
        try:
            user_id = int(kwargs['pk'])
            user = User.objects.get(id=user_id)
        except (ValueError, User.DoesNotExist):
            return Response({'error': 'Invalid user id'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            if request.data.get("new_password") != request.data.get("confirm_password"):
                return Response({"password": "Password and confirm password does not match!"},
                                status=status.HTTP_400_BAD_REQUEST)

            user.set_password(request.data.get("new_password"))
            user.save()

            response = {
                'status': 'success',
                'code': status.HTTP_200_OK,
                'message': 'Password updated successfully',
                'data': []
            }
            return Response(response)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfileIdView(generics.CreateAPIView):
    serializer_class = UserProfileSerializer


class ProfileListView(GenericViewSet, ListModelMixin):
    serializers_class = ProfileListSerializer
    queryset = UserProfile.objects.all()

    def list(self, request, *args, **kwargs):
        user = self.request.query_params.get('user_id')
        serializer = ProfileListSerializer(UserProfile.objects.filter(user__id=user), many=True,
                     context={'request': request})
        # serializer.data[0]['user']['profile_pic'] = absolute_url+serializer.data[0]['user']['profile_pic']
        # serializer.data[0]['image'] = absolute_url+serializer.data[0]['image']
        return Response(serializer.data)


class UserLogoutView(mixins.DestroyModelMixin, generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def delete(self, request, *args, **kwargs):
        try:
            auth_token = Token.objects.get(user=request.user)
            auth_token.delete()
            request.user.auth_token.delete()
        except Token.DoesNotExist:
            pass

        self.logout(request)
        return Response({'detail': 'User logged out successfully'})

    def logout(self, request):
        self.request.session.flush()
        self.request.user.authenticated = False
        logout(request)


class TokenRefreshViewset(viewsets.GenericViewSet):
    permission_classes = (permissions.AllowAny,)
    serializer_class = TokenRefreshSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        refresh = serializer.validated_data['refresh']

        response = TokenRefreshView.as_view()(request._request)
        return Response(response.data)
