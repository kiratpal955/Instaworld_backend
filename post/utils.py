import os

from rest_framework_simplejwt.tokens import RefreshToken


def user_upload_path(instance, filename):

    username = instance.user.username
    ext = filename.split('.')[-1]
    if ext in ['jpg', 'jpeg', 'png', 'gif']:
        folder = 'images'
    elif ext in ['mp4', 'avi', 'mov', 'mkv']:
        folder = 'videos'
    else:
        raise ValueError('Unsupported file format')
    return os.path.join(username, folder, filename)


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }