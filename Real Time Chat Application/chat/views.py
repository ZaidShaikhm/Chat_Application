from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import JsonResponse
from django.contrib import messages
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.utils import timezone
import os

from .models import Conversation, Group, GroupMembership, Message, Attachment
from accounts.models import UserProfile
from .notifications import notify_offline_private_recipient, notify_offline_group_members


def home_view(request):
    """Landing home page describing the project and features."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    total_users = User.objects.count()
    return render(request, 'home.html', {
        'total_users': total_users
    })


@login_required
def dashboard_view(request):
    """
    Main user dashboard displaying:
    - User profile overview
    - Search registered users
    - Registered users list with online/offline status
    - Recent private conversations with unread counts
    - Joined and available chat groups
    """
    query = request.GET.get('q', '').strip()
    
    # Registered users list (exclude self)
    users_queryset = User.objects.exclude(id=request.user.id).select_related('profile')
    if query:
        users_queryset = users_queryset.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query)
        )
    users_list = users_queryset.order_by('-profile__is_online', 'username')

    # Recent conversations of current user
    conversations = Conversation.objects.filter(
        Q(user1=request.user) | Q(user2=request.user)
    ).prefetch_related('messages').order_by('-updated_at')

    # Build conversation card data
    recent_chats = []
    for conv in conversations:
        other_user = conv.get_other_user(request.user)
        last_msg = conv.get_last_message()
        unread_count = conv.unread_count_for(request.user)
        recent_chats.append({
            'conversation': conv,
            'other_user': other_user,
            'last_message': last_msg,
            'unread_count': unread_count,
        })

    # Groups
    user_groups = request.user.chat_groups.all().order_by('-updated_at')
    all_groups = Group.objects.all().order_by('-created_at')

    context = {
        'profile': getattr(request.user, 'profile', None),
        'users_list': users_list,
        'recent_chats': recent_chats,
        'user_groups': user_groups,
        'all_groups': all_groups,
        'query': query,
        'total_registered': User.objects.count(),
        'active_conversations_count': conversations.count(),
    }
    return render(request, 'dashboard.html', context)


@login_required
def private_chat_view(request, username):
    """
    One-to-one private chat view.
    Retrieves or starts conversation with another user,
    loads previous conversation history, and handles real-time WebSocket connection.
    """
    if username == request.user.username:
        messages.warning(request, "You cannot chat with yourself.")
        return redirect('dashboard')

    other_user = get_object_or_404(User.objects.select_related('profile'), username=username)
    conversation = Conversation.get_or_create_conversation(request.user, other_user)

    # Mark all unread messages from other user as read
    conversation.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)

    # Load messages with attachments
    chat_messages = conversation.messages.prefetch_related('attachments').select_related('sender__profile').all()

    # Load sidebar data (recent conversations)
    conversations = Conversation.objects.filter(
        Q(user1=request.user) | Q(user2=request.user)
    ).order_by('-updated_at')
    
    sidebar_chats = []
    for conv in conversations:
        partner = conv.get_other_user(request.user)
        last_msg = conv.get_last_message()
        unread = conv.unread_count_for(request.user)
        sidebar_chats.append({
            'conversation': conv,
            'other_user': partner,
            'last_message': last_msg,
            'unread_count': unread,
            'is_active': (partner == other_user)
        })

    context = {
        'conversation': conversation,
        'other_user': other_user,
        'chat_messages': chat_messages,
        'sidebar_chats': sidebar_chats,
        'profile': getattr(request.user, 'profile', None),
    }
    return render(request, 'chat.html', context)


@login_required
def group_chat_view(request, group_id):
    """
    Group messaging view.
    Displays group details, members, message history with sender info, and WebSocket channel.
    """
    group = get_object_or_404(Group.objects.prefetch_related('members'), id=group_id)

    # Check if user is a member of this group
    membership = GroupMembership.objects.filter(group=group, user=request.user).first()
    if not membership:
        messages.warning(request, f"You are not a member of '{group.name}'. Please join the group to participate.")
        return redirect('dashboard')

    chat_messages = group.messages.prefetch_related('attachments').select_related('sender__profile').all()
    memberships = group.memberships.select_related('user__profile').order_by('role', 'user__username')
    
    # Available users who are NOT yet in the group (for adding members modal)
    existing_member_ids = group.members.values_list('id', flat=True)
    available_users = User.objects.exclude(id__in=existing_member_ids).select_related('profile')

    # Sidebar groups
    sidebar_groups = request.user.chat_groups.all().order_by('-updated_at')

    context = {
        'group': group,
        'chat_messages': chat_messages,
        'memberships': memberships,
        'available_users': available_users,
        'sidebar_groups': sidebar_groups,
        'is_admin': group.memberships.filter(user=request.user, role='admin').exists() or group.created_by == request.user,
        'profile': getattr(request.user, 'profile', None),
    }
    return render(request, 'group_chat.html', context)


@login_required
def create_group_view(request):
    """Handles creating a new chat group with custom name, description, avatar, and initial members."""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        avatar = request.FILES.get('avatar')
        selected_members = request.POST.getlist('members')

        if not name:
            messages.error(request, "Please enter a valid group name.")
            return redirect('dashboard')

        group = Group.objects.create(
            name=name,
            description=description,
            avatar=avatar,
            created_by=request.user
        )

        # Add creator as Admin
        GroupMembership.objects.create(group=group, user=request.user, role='admin')

        # Add selected members
        for uid in selected_members:
            try:
                member_user = User.objects.get(id=uid)
                if member_user != request.user:
                    GroupMembership.objects.get_or_create(group=group, user=member_user, role='member')
            except User.DoesNotExist:
                pass

        messages.success(request, f"Group '{group.name}' created successfully!")
        return redirect('group_chat', group_id=group.id)

    return redirect('dashboard')


@login_required
def add_group_member_view(request, group_id):
    """Allows adding registered users to an existing group."""
    group = get_object_or_404(Group, id=group_id)

    if request.method == 'POST':
        user_ids = request.POST.getlist('members')
        added_count = 0
        for uid in user_ids:
            try:
                user = User.objects.get(id=uid)
                membership, created = GroupMembership.objects.get_or_create(group=group, user=user)
                if created:
                    added_count += 1
            except User.DoesNotExist:
                continue

        if added_count > 0:
            messages.success(request, f"Added {added_count} new member(s) to {group.name}.")
        else:
            messages.info(request, "No new members were added.")

    return redirect('group_chat', group_id=group.id)


@login_required
def leave_group_view(request, group_id):
    """Allows a user to leave a group chat room."""
    group = get_object_or_404(Group, id=group_id)
    membership = GroupMembership.objects.filter(group=group, user=request.user).first()

    if not membership:
        messages.warning(request, f"You are not a member of '{group.name}'.")
        return redirect('dashboard')

    if request.method == 'POST':
        remaining_memberships = group.memberships.exclude(user=request.user)

        # If user is the only member, deleting membership means group is empty -> delete group
        if not remaining_memberships.exists():
            group_name = group.name
            group.delete()
            messages.info(request, f"You left '{group_name}'. Since you were the only member, the group has been deleted.")
            return redirect('dashboard')

        # If user was the creator or admin, ensure there's at least one admin remaining
        if membership.role == 'admin' or group.created_by == request.user:
            admin_exists = remaining_memberships.filter(role='admin').exists()
            if not admin_exists:
                next_admin_membership = remaining_memberships.order_by('joined_at').first()
                if next_admin_membership:
                    next_admin_membership.role = 'admin'
                    next_admin_membership.save(update_fields=['role'])
                    if group.created_by == request.user:
                        group.created_by = next_admin_membership.user
                        group.save(update_fields=['created_by'])

        # Delete membership
        membership.delete()

        # Create system notification message in the group
        system_msg = Message.objects.create(
            sender=request.user,
            group=group,
            content=f"{request.user.get_full_name() or request.user.username} left the group."
        )
        group.save()

        # Broadcast leave event to remaining group members via WebSockets
        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                f'group_{group.id}',
                {
                    'type': 'chat_message_forward',
                    'message_id': system_msg.id,
                    'message': system_msg.content,
                    'sender_id': request.user.id,
                    'sender_username': request.user.username,
                    'sender_name': 'System',
                    'sender_avatar': None,
                    'timestamp': system_msg.timestamp.isoformat(),
                    'time_display': timezone.localtime(system_msg.timestamp).strftime('%I:%M %p'),
                    'attachments': []
                }
            )

        messages.success(request, f"You have left '{group.name}'.")
        return redirect('dashboard')

    return redirect('group_chat', group_id=group.id)


@login_required
def delete_group_view(request, group_id):
    """Allows group creator or admin to delete the group permanently."""
    group = get_object_or_404(Group, id=group_id)

    is_admin = (
        group.created_by == request.user or
        group.memberships.filter(user=request.user, role='admin').exists() or
        request.user.is_superuser or
        request.user.is_staff or
        request.user.username == 'admin'
    )

    if not is_admin:
        messages.error(request, "Permission denied: Only group administrators or the creator can delete this group.")
        return redirect('group_chat', group_id=group.id)

    if request.method == 'POST':
        group_name = group.name
        # Delete group (cascades to memberships, messages, attachments in SQLite)
        group.delete()
        messages.success(request, f"Group '{group_name}' has been deleted successfully.")
        return redirect('dashboard')

    return redirect('group_chat', group_id=group.id)


@login_required
def join_group_view(request, group_id):
    """Allows a user to join an open group from the dashboard."""
    group = get_object_or_404(Group, id=group_id)
    membership, created = GroupMembership.objects.get_or_create(
        group=group,
        user=request.user,
        defaults={'role': 'member'}
    )

    if created:
        join_msg = Message.objects.create(
            sender=request.user,
            group=group,
            content=f"{request.user.get_full_name() or request.user.username} joined the group."
        )
        group.save()

        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                f'group_{group.id}',
                {
                    'type': 'chat_message_forward',
                    'message_id': join_msg.id,
                    'message': join_msg.content,
                    'sender_id': request.user.id,
                    'sender_username': request.user.username,
                    'sender_name': 'System',
                    'sender_avatar': None,
                    'timestamp': join_msg.timestamp.isoformat(),
                    'time_display': timezone.localtime(join_msg.timestamp).strftime('%I:%M %p'),
                    'attachments': []
                }
            )
        messages.success(request, f"You joined '{group.name}'!")
    else:
        messages.info(request, f"You are already a member of '{group.name}'.")

    return redirect('group_chat', group_id=group.id)


@login_required
def remove_group_member_view(request, group_id, user_id):
    """Allows group admin to remove a member from the group."""
    group = get_object_or_404(Group, id=group_id)

    is_admin = (
        group.created_by == request.user or
        group.memberships.filter(user=request.user, role='admin').exists() or
        request.user.is_superuser or
        request.user.is_staff or
        request.user.username == 'admin'
    )

    if not is_admin:
        messages.error(request, "Permission denied: Only group administrators can remove members.")
        return redirect('group_chat', group_id=group.id)

    target_user = get_object_or_404(User, id=user_id)
    if target_user == request.user:
        messages.warning(request, "Use the 'Leave Group' option to remove yourself.")
        return redirect('group_chat', group_id=group.id)

    membership = GroupMembership.objects.filter(group=group, user=target_user).first()
    if membership:
        membership.delete()

        # Post system message
        system_msg = Message.objects.create(
            sender=request.user,
            group=group,
            content=f"{target_user.get_full_name() or target_user.username} was removed by {request.user.get_full_name() or request.user.username}."
        )
        group.save()

        # Broadcast via WebSockets
        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                f'group_{group.id}',
                {
                    'type': 'chat_message_forward',
                    'message_id': system_msg.id,
                    'message': system_msg.content,
                    'sender_id': request.user.id,
                    'sender_username': request.user.username,
                    'sender_name': 'System',
                    'sender_avatar': None,
                    'timestamp': system_msg.timestamp.isoformat(),
                    'time_display': timezone.localtime(system_msg.timestamp).strftime('%I:%M %p'),
                    'attachments': []
                }
            )

        messages.success(request, f"Removed {target_user.get_full_name() or target_user.username} from {group.name}.")
    else:
        messages.info(request, "User is not a member of this group.")

    return redirect('group_chat', group_id=group.id)


@login_required
def file_upload_view(request):
    """
    Handles file/image attachments via AJAX multipart upload.
    Saves Message and Attachment in SQLite and broadcasts via Channels WebSocket!
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)

    uploaded_file = request.FILES.get('file')
    if not uploaded_file:
        return JsonResponse({'error': 'No file uploaded'}, status=400)

    conversation_id = request.POST.get('conversation_id')
    group_id = request.POST.get('group_id')
    content = request.POST.get('content', '').strip()

    # Determine file size string
    size_bytes = uploaded_file.size
    if size_bytes < 1024:
        formatted_size = f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        formatted_size = f"{size_bytes / 1024:.1f} KB"
    else:
        formatted_size = f"{size_bytes / (1024 * 1024):.1f} MB"

    # Determine file type
    ext = os.path.splitext(uploaded_file.name)[1].lower()
    if ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']:
        file_type = 'image'
    elif ext in ['.pdf']:
        file_type = 'pdf'
    elif ext in ['.doc', '.docx', '.txt', '.xls', '.xlsx', '.ppt', '.pptx', '.zip']:
        file_type = 'document'
    else:
        file_type = 'file'

    conversation = None
    group = None
    channel_room = None

    if conversation_id:
        conversation = get_object_or_404(Conversation, id=conversation_id)
        channel_room = f'chat_{conversation.id}'
    elif group_id:
        group = get_object_or_404(Group, id=group_id)
        channel_room = f'group_{group.id}'
    else:
        return JsonResponse({'error': 'Missing conversation_id or group_id'}, status=400)

    # Create Message
    msg = Message.objects.create(
        sender=request.user,
        conversation=conversation,
        group=group,
        content=content if content else f"Shared an attachment: {uploaded_file.name}"
    )

    # Create Attachment
    attachment = Attachment.objects.create(
        message=msg,
        file=uploaded_file,
        file_name=uploaded_file.name,
        file_type=file_type,
        file_size=formatted_size
    )

    if conversation:
        conversation.save()  # update timestamp
    if group:
        group.save()

    sender_avatar = None
    if hasattr(request.user, 'profile') and request.user.profile.profile_picture:
        sender_avatar = request.user.profile.profile_picture.url

    # Broadcast file message via Django Channels
    channel_layer = get_channel_layer()
    if channel_room and channel_layer:
        async_to_sync(channel_layer.group_send)(
            channel_room,
            {
                'type': 'chat_message_forward',
                'message_id': msg.id,
                'message': msg.content,
                'sender_id': request.user.id,
                'sender_username': request.user.username,
                'sender_name': request.user.get_full_name() or request.user.username,
                'sender_avatar': sender_avatar,
                'timestamp': msg.timestamp.isoformat(),
                'time_display': timezone.localtime(msg.timestamp).strftime('%I:%M %p'),
                'attachments': [{
                    'id': attachment.id,
                    'file_url': attachment.file.url,
                    'file_name': attachment.file_name,
                    'file_type': attachment.file_type,
                    'file_size': attachment.file_size,
                    'is_image': attachment.is_image
                }]
            }
        )

    # Trigger email notifications to offline recipients
    if conversation:
        notify_offline_private_recipient(conversation, request.user, msg.content, has_attachment=True)
    elif group:
        notify_offline_group_members(group, request.user, msg.content, has_attachment=True)

    return JsonResponse({
        'success': True,
        'message_id': msg.id,
        'file_url': attachment.file.url,
        'file_name': attachment.file_name,
        'file_type': attachment.file_type,
        'file_size': attachment.file_size,
        'is_image': attachment.is_image
    })
