from django.db import models
from django.contrib.auth.models import User
from django.db.models import Q
import os


class Conversation(models.Model):
    """
    Stores private one-to-one conversation between two users.
    """
    user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversations_initiated')
    user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversations_received')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        constraints = [
            models.UniqueConstraint(fields=['user1', 'user2'], name='unique_conversation_pair')
        ]

    def __str__(self):
        return f"Chat: {self.user1.username} & {self.user2.username}"

    @classmethod
    def get_or_create_conversation(cls, user_a, user_b):
        """
        Ensures a single conversation instance between two users regardless of who initiated.
        Orders by user ID for uniqueness.
        """
        if user_a.id > user_b.id:
            u1, u2 = user_b, user_a
        else:
            u1, u2 = user_a, user_b
        
        conversation, created = cls.objects.get_or_create(user1=u1, user2=u2)
        return conversation

    def get_other_user(self, current_user):
        """Returns the other participant in the conversation."""
        return self.user2 if self.user1 == current_user else self.user1

    def get_last_message(self):
        """Returns the most recent message in this conversation."""
        return self.messages.order_by('-timestamp').first()

    def unread_count_for(self, user):
        """Returns count of unread messages sent to this user."""
        return self.messages.filter(is_read=False).exclude(sender=user).count()


class Group(models.Model):
    """
    Stores group chat room information.
    """
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True, default='')
    avatar = models.ImageField(upload_to='group_avatars/', blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='groups_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    members = models.ManyToManyField(User, through='GroupMembership', related_name='chat_groups')

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return self.name

    def get_last_message(self):
        """Returns the most recent message in this group."""
        return self.messages.order_by('-timestamp').first()


class GroupMembership(models.Model):
    """
    Stores membership details of a user in a group.
    """
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('member', 'Member'),
    )
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='group_memberships')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('group', 'user')

    def __str__(self):
        return f"{self.user.username} in {self.group.name} ({self.role})"


class Message(models.Model):
    """
    Stores text and attachment references for private or group conversations.
    """
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, null=True, blank=True, related_name='messages')
    group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True, blank=True, related_name='messages')
    content = models.TextField(blank=True, default='')
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        if self.conversation:
            return f"[{self.timestamp.strftime('%H:%M')}] {self.sender.username} -> Conv #{self.conversation.id}: {self.content[:30]}"
        elif self.group:
            return f"[{self.timestamp.strftime('%H:%M')}] {self.sender.username} -> Group {self.group.name}: {self.content[:30]}"
        return f"[{self.timestamp.strftime('%H:%M')}] {self.sender.username}: {self.content[:30]}"


class Attachment(models.Model):
    """
    Stores file attachment information linked to a chat message.
    """
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='attachments/')
    file_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=50, blank=True, default='file')
    file_size = models.CharField(max_length=50, blank=True, default='')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file_name

    @property
    def is_image(self):
        ext = os.path.splitext(self.file_name)[1].lower()
        return ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']
