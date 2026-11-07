from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    """
    Stores profile information, avatar, and online status for each registered user.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.CharField(max_length=250, blank=True, default='Hey there! I am using DjangoChat.')
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(auto_now=True)
    email_notifications = models.BooleanField(
        default=True,
        help_text="Receive email notifications on registered Gmail when offline"
    )

    def __str__(self):
        return f"{self.user.username}'s Profile"

    @property
    def full_name(self):
        full = f"{self.user.first_name} {self.user.last_name}".strip()
        return full if full else self.user.username

    @property
    def avatar_url(self):
        if self.profile_picture and hasattr(self.profile_picture, 'url'):
            return self.profile_picture.url
        return None


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
    else:
        # Save profile if it exists
        if hasattr(instance, 'profile'):
            instance.profile.save()
