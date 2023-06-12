import string
from datetime import timezone, datetime
from random import random
from post.models import Post
from django.contrib.auth.models import User
from rest_framework import serializers
import re
import sys

from post.models import Post
from .constants import absolute_url

sys.path.append("..")
from .models import UserProfile

import random
from django.contrib.auth import get_user_model
from django.utils import timezone

from account.utility import send_otp, validate_phone_number, send_otp_on_phone


class UserSerializer(serializers.ModelSerializer):
    """ Serializer for showing post of the follower user follow"""

    profile_pic = serializers.ImageField(source='userprofile.image', read_only=True)

    class Meta:
        model = User
        exclude = ['password', 'last_login', 'is_superuser', 'is_staff', 'date_joined', 'groups', 'user_permissions']


class UserRegisterSerializer(serializers.ModelSerializer):
    """Serializer to Register user"""
    username = serializers.CharField(trim_whitespace=False, required=True)
    first_name = serializers.CharField(max_length=20, min_length=2, required=True,
                                       trim_whitespace=False)
    last_name = serializers.CharField(max_length=20, min_length=2, required=True,
                                      trim_whitespace=False)

    password = serializers.CharField(max_length=20, min_length=8, required=True,
                                     write_only=True, trim_whitespace=False)
    confirm_password = serializers.CharField(max_length=20, min_length=8, required=True,
                                             write_only=True)

    is_active = serializers.BooleanField(default=False)

    class Meta:
        model = User
        fields = ('id', 'username', 'password', 'confirm_password', 'first_name', 'last_name', 'is_active')

    def validate_password(self, value, user=None):
        regex = re.compile(r'^(?=.*[!@#$%^&*()_+\-=[\]{};:\'"\\|,.<>/?])(?=.*[A-Z])(?=.*[a-z])(?=.*\d)[^\s]{8,}$')
        if not regex.match(value):
            raise serializers.ValidationError("Password must contain at least one special character, one capital "
                                              "letter, one small letter, and one number, with a length of at least 8 "
                                              "and no spaces.")
        return value

    def validate_username(self, value):
        if any(char not in string.ascii_letters + string.digits + string.punctuation for char in value):
            raise serializers.ValidationError(
                "Username should contain alphanumeric characters and special characters only.")
        if not any(char.isalpha() for char in value):
            raise serializers.ValidationError("Username should contain at least one alphabet.")
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exist")
        return value

    def validate_first_name(self, value):
        """
            Field level validation to validate first name
        """
        if not value.isalpha() or ' ' in value:
            raise serializers.ValidationError("Invalid First name. Only Alphabets are allowed.")
        return value

    def validate_last_name(self, value):
        """
            Field level validation to validate last name
        """
        if not value.isalpha() or ' ' in value:
            raise serializers.ValidationError("Invalid last name. Only Alphabets are allowed.")
        return value

    def validate(self, data):
        """
            Object level validation to check weather the given field exist or not and to match passwords
        """
        email = data.get('email')
        password = data.get('password')
        c_password = data.get('confirm_password')

        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError("Email already exists!")
        if password != c_password:
            raise serializers.ValidationError("Password and confirm password does not match!")
        return data

    def create(self, validated_data):
        """
            create function to create validated user data
        """
        user = User.objects.create_user(
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            username=validated_data['username'],
            password=validated_data['password'],
            is_active=validated_data['is_active']
        )
        user_profile = UserProfile.objects.create(user=user)
        return user, user_profile


class UserLogInSerializer(serializers.ModelSerializer):
    """Serializer to Login user"""
    username = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ("username", "password")


class UserChangePasswordSerializer(serializers.ModelSerializer):
    """Serializer for changing user password"""
    new_password = serializers.CharField(max_length=20, write_only=True, style={'input_type': 'password'})
    confirm_password = serializers.CharField(max_length=20, write_only=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ['password', 'new_password', 'confirm_password']


class DeleteUserSerializer(serializers.ModelSerializer):
    """Serializer to delete user for User model"""

    class Meta:
        model = User
        fields = '__all__'


class UserSearchSerializer(serializers.ModelSerializer):
    profile_pic = serializers.ImageField(source='userprofile.image', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'profile_pic']


class ProfileSerializer(serializers.ModelSerializer):
    follower_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()
    post_count = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        exclude = ('followers', 'otp', 'otp_at')

    def get_follower_count(self, obj):
        return obj.followers.count()

    def get_following_count(self, obj):
        return obj.user.following.count()

    def get_post_count(self, obj):
        post_count = Post.objects.filter(user=obj.user).count()
        return post_count


class FollowersSerializer(serializers.ModelSerializer):
    followers = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = ('followers',)

    def get_followers(self, obj):
        request = self.context.get('request')
        return [{'id': user.id, 'username': user.username,
                 'profile': {'profile_pic': absolute_url + "/media/" + str(user.userprofile.image)}}
                for user in obj.followers.all()]


class FollowingSerializer(serializers.ModelSerializer):
    following = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = ('following',)

    def get_following(self, obj):
        current_user = obj.user
        request = self.context.get('request')
        return [{'id': profile.user.id, 'username': profile.user.username,
                 'profile': {'profile_pic': absolute_url + "/media/" + str(profile.image)}}
                for profile in current_user.following.all()]


User = get_user_model()


class VerifyOTPSerializer(serializers.Serializer):
    otp = serializers.CharField()

    def validate(self, attrs):
        otp = attrs['otp']
        otp_obj = UserProfile.objects.filter(otp=otp).first()

        if not otp_obj:
            raise serializers.ValidationError('Invalid OTP')
        elif (timezone.now() - otp_obj.otp_at).seconds > 300:
            raise serializers.ValidationError('OTP expired')
        elif otp_obj.otp == otp:
            user = otp_obj.user
            user.is_active = True
            user.save()
            attrs['user'] = user
            return attrs

    def create(self, validated_data):
        otp = validated_data.get('otp')
        user = validated_data.get('user')
        otp_obj = UserProfile.objects.filter(otp=otp).first()
        return otp_obj


class UserProfileOTPSerializer(serializers.ModelSerializer):
    date_of_birth = serializers.DateField(required=True)
    phone_number = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)

    class Meta:
        model = UserProfile
        fields = ('id', 'otp', 'otp_at', 'phone_number', 'email', 'date_of_birth')

    def generate_otp(self, user_profile, validated_data):
        date_of_birth = validated_data.get('date_of_birth')
        email = validated_data.get('email')
        phone_number = validated_data.get('phone_number')
        user = user_profile.user
        otp = str(random.randint(100000, 999999))

        if phone_number:
            validate_phone_number(self, phone_number)
            send_otp_on_phone(self, phone_number, otp)
            user_profile.phone_number = phone_number

        if email:
            user.email = email
            user.save()
            send_otp(self, email, otp)

        user_profile.otp = otp
        user_profile.otp_at = datetime.now()
        user_profile.date_of_birth = date_of_birth
        user_profile.save()
        return otp

    def validate_email(self, data):
        email = data
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError("Email already exists!")
        return data

    def validate_phone_number(self, data):
        phone_number = data
        if UserProfile.objects.filter(phone_number=phone_number).exists():
            raise serializers.ValidationError("Phone Number already exists!")
        return data

    def validate(self, attrs):
        if not attrs.get('phone_number') and not attrs.get('email'):
            raise serializers.ValidationError("Either phone number or email is required")
        return attrs


class UserDetailSerializer(UserSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name"]


class ProfileFollowerSerializer(serializers.ModelSerializer):
    user = UserDetailSerializer()
    profile_pic = serializers.ImageField(source='image', read_only=True)

    class Meta:
        model = UserProfile
        fields = ['id', 'profile_pic', 'user']


class UserFollowSerializer(serializers.ModelSerializer):
    following = serializers.SerializerMethodField()

    # has_follow = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = ('user', 'following')

    # def get_has_follow(self, obj):
    #     user = self.context['request'].user
    #     return user.is_authenticated and user.following.filter(pk=obj.id).exists()

    def get_following(self, obj):
        user_followings = ProfileFollowerSerializer(obj.user.following.all(), many=True)
        print(obj.user.following.count())
        return user_followings.data


class TokenSerializer(serializers.Serializer):
    token = serializers.CharField()


# class UserFollowSerializer(serializers.ModelSerializer):
#     # following = UserSerializer(read_only=True, many=True)
#     followers = UserSerializer(read_only=True, many=True)
#
#     class Meta:
#         model = UserProfile
#         fields = ('user', 'followers')


class ForgotPasswordOTPSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=True)
    phone_number = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)

    class Meta:
        model = UserProfile
        fields = ('id', 'otp', 'otp_at', 'phone_number', 'email', 'username')

    def generate_otp(self, user_profile, validated_data):
        username = validated_data.get('username')
        email = validated_data.get('email')
        phone_number = validated_data.get('phone_number')
        user = user_profile.user
        otp = str(random.randint(100000, 999999))

        if username and User.objects.filter(username=username).exists():
            user = User.objects.get(username=username)
            if email:
                if user.email != email:
                    raise serializers.ValidationError("The email provided does not match the saved email.")
                else:
                    send_otp(self, email, otp)
            if phone_number:
                if hasattr(user, 'phone_number') and user.profile.phone_number != phone_number:
                    raise serializers.ValidationError(
                        "The phone number provided does not match the saved phone number.")
                else:
                    validate_phone_number(self, phone_number)
                    send_otp_on_phone(self, phone_number, otp)

            user_profile.otp_at = datetime.now()
            user_profile.otp = otp
            user_profile.save()
            return otp, user

    def validate(self, attrs):
        if not attrs.get('phone_number') and not attrs.get('email'):
            raise serializers.ValidationError("Either phone number or email is required for Forgot Password")
        return attrs


class ForgotPasswordSerializer(serializers.ModelSerializer):
    new_password = serializers.CharField(max_length=20, write_only=True, style={'input_type': 'password'})
    confirm_password = serializers.CharField(max_length=20, write_only=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ['new_password', 'confirm_password']


class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(write_only=True)
    user = UserSerializer(read_only=True)
    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = UserProfile
        fields = ('id', 'username', 'user', 'profile', 'phone_number', 'image')

    def create(self, validated_data):
        username = validated_data.pop('username')
        try:
            user = User.objects.get(username=username)
            user_profile = UserProfile.objects.get(user=user)
            return user_profile
        except User.DoesNotExist:
            raise serializers.ValidationError('User does not exist.')


class ProfileListSerializer(ProfileSerializer):
    user = UserSerializer(read_only=True)
    is_followed = serializers.SerializerMethodField()

    def get_post_count(self, obj):
        post_count = Post.objects.filter(user=obj.user).count()
        return post_count

    def get_is_followed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            user = request.user
            return user in obj.followers.all()
        return False

    class Meta:
        model = UserProfile
        exclude = ('followers', 'otp', 'otp_at')


class TokenRefreshSerializer(serializers.Serializer):
    refresh = serializers.CharField()
