from django.contrib import admin
from .models import Conversation, Group, GroupMembership, Message, Attachment


class AttachmentInline(admin.TabularInline):
    model = Attachment
    extra = 0


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user1', 'user2', 'created_at', 'updated_at')
    search_fields = ('user1__username', 'user2__username')


class GroupMembershipInline(admin.TabularInline):
    model = GroupMembership
    extra = 1


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_by', 'created_at', 'updated_at')
    search_fields = ('name', 'description', 'created_by__username')
    inlines = [GroupMembershipInline]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'sender', 'conversation', 'group', 'content', 'timestamp', 'is_read')
    list_filter = ('is_read', 'timestamp')
    search_fields = ('sender__username', 'content')
    inlines = [AttachmentInline]


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ('file_name', 'message', 'file_type', 'file_size', 'uploaded_at')
    search_fields = ('file_name',)
