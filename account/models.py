from django.contrib.auth.models import User
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField


# Create your models here.
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to="img/", null=True, blank=True)
    bio = models.CharField(max_length=200, null=True, blank=True)
    followers = models.ManyToManyField(User, related_name='following', blank=True)
    created_on = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    otp = models.CharField(max_length=10, blank=True, null=True)
    otp_at = models.DateTimeField(blank=True, null=True)
    phone_number = PhoneNumberField(max_length=20, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    objects = models.Model

    def __str__(self):
        return f"{self.bio}"
