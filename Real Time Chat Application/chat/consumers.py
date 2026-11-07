import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import Conversation, Group, Message, Attachment
from accounts.models import UserProfile
from django.utils import timezone
from .notifications import notify_offline_private_recipient, notify_offline_group_members


class PrivateChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for one-to-one private chats.
    Handles message delivery, typing indicator, and real-time read receipts.
    """
    async def connect(self):
        self.user = self.scope.get('user')

        if not self.user or not self.user.is_authenticated:
            await self.close()
            return

        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.room_group_name = f'chat_{self.conversation_id}'

        # Verify that the user is a participant of this conversation
        is_participant = await self.check_participant(self.conversation_id, self.user)
        if not is_participant:
            await self.close()
            return

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        # Update online status
        await self.set_user_online(self.user, True)

        # Notify other user that current user is online
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_status',
                'user_id': self.user.id,
                'username': self.user.username,
                'status': 'online'
            }
        )

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            if hasattr(self, 'user') and self.user.is_authenticated:
                await self.set_user_online(self.user, False)

            # Broadcast offline status
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_status',
                    'user_id': self.user.id,
                    'username': self.user.username,
                    'status': 'offline'
                }
            )

            # Leave room group
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')

        if message_type == 'chat_message':
            content = data.get('message', '').strip()
            if not content:
                return

            # Save message to database
            msg = await self.save_message(self.conversation_id, self.user, content)

            # Send message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message_forward',
                    'message_id': msg['id'],
                    'message': msg['content'],
                    'sender_id': self.user.id,
                    'sender_username': self.user.username,
                    'sender_name': self.user.get_full_name() or self.user.username,
                    'sender_avatar': msg['sender_avatar'],
                    'timestamp': msg['timestamp'],
                    'time_display': msg['time_display'],
                    'attachments': []
                }
            )

            # Trigger email notification to offline recipient
            await self.send_offline_email_notification(self.conversation_id, self.user, content)

        elif message_type == 'typing':
            is_typing = data.get('is_typing', False)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'typing_status',
                    'sender_id': self.user.id,
                    'sender_username': self.user.username,
                    'is_typing': is_typing
                }
            )

        elif message_type == 'mark_read':
            await self.mark_messages_read(self.conversation_id, self.user)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'read_receipt',
                    'reader_id': self.user.id
                }
            )

    async def chat_message_forward(self, event):
        await self.send(text_data=json.dumps(event))

    async def typing_status(self, event):
        # Do not bounce back to self
        if event['sender_id'] != self.user.id:
            await self.send(text_data=json.dumps(event))

    async def user_status(self, event):
        if event['user_id'] != self.user.id:
            await self.send(text_data=json.dumps(event))

    async def read_receipt(self, event):
        await self.send(text_data=json.dumps(event))

    @database_sync_to_async
    def check_participant(self, conversation_id, user):
        try:
            conv = Conversation.objects.get(id=conversation_id)
            return conv.user1 == user or conv.user2 == user
        except Conversation.DoesNotExist:
            return False

    @database_sync_to_async
    def set_user_online(self, user, status):
        try:
            profile = user.profile
            profile.is_online = status
            profile.save(update_fields=['is_online', 'last_seen'])
        except Exception:
            pass

    @database_sync_to_async
    def save_message(self, conversation_id, user, content):
        conv = Conversation.objects.get(id=conversation_id)
        msg = Message.objects.create(
            sender=user,
            conversation=conv,
            content=content
        )
        conv.save()  # update updated_at timestamp

        avatar_url = None
        if hasattr(user, 'profile') and user.profile.profile_picture:
            avatar_url = user.profile.profile_picture.url

        return {
            'id': msg.id,
            'content': msg.content,
            'timestamp': msg.timestamp.isoformat(),
            'time_display': timezone.localtime(msg.timestamp).strftime('%I:%M %p'),
            'sender_avatar': avatar_url
        }

    @database_sync_to_async
    def send_offline_email_notification(self, conversation_id, user, content):
        try:
            conv = Conversation.objects.get(id=conversation_id)
            notify_offline_private_recipient(conv, user, content)
        except Exception:
            pass

    @database_sync_to_async
    def mark_messages_read(self, conversation_id, user):
        conv = Conversation.objects.get(id=conversation_id)
        conv.messages.filter(is_read=False).exclude(sender=user).update(is_read=True)


class GroupChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for group chats.
    Handles broadcasting to all members, typing indicator, and real-time updates.
    """
    async def connect(self):
        self.user = self.scope.get('user')

        if not self.user or not self.user.is_authenticated:
            await self.close()
            return

        self.group_id = self.scope['url_route']['kwargs']['group_id']
        self.room_group_name = f'group_{self.group_id}'

        # Check membership
        is_member = await self.check_membership(self.group_id, self.user)
        if not is_member:
            await self.close()
            return

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        # Update online status
        await self.set_user_online(self.user, True)

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            if hasattr(self, 'user') and self.user.is_authenticated:
                await self.set_user_online(self.user, False)

            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')

        if message_type == 'chat_message':
            content = data.get('message', '').strip()
            if not content:
                return

            msg = await self.save_group_message(self.group_id, self.user, content)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message_forward',
                    'message_id': msg['id'],
                    'message': msg['content'],
                    'sender_id': self.user.id,
                    'sender_username': self.user.username,
                    'sender_name': self.user.get_full_name() or self.user.username,
                    'sender_avatar': msg['sender_avatar'],
                    'timestamp': msg['timestamp'],
                    'time_display': msg['time_display'],
                    'attachments': []
                }
            )

            # Trigger email notifications to offline group members
            await self.send_group_offline_email_notifications(self.group_id, self.user, content)

        elif message_type == 'typing':
            is_typing = data.get('is_typing', False)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'typing_status',
                    'sender_id': self.user.id,
                    'sender_username': self.user.username,
                    'sender_name': self.user.get_full_name() or self.user.username,
                    'is_typing': is_typing
                }
            )

    async def chat_message_forward(self, event):
        await self.send(text_data=json.dumps(event))

    async def typing_status(self, event):
        if event['sender_id'] != self.user.id:
            await self.send(text_data=json.dumps(event))

    @database_sync_to_async
    def check_membership(self, group_id, user):
        try:
            group = Group.objects.get(id=group_id)
            return group.members.filter(id=user.id).exists()
        except Group.DoesNotExist:
            return False

    @database_sync_to_async
    def save_group_message(self, group_id, user, content):
        group = Group.objects.get(id=group_id)
        msg = Message.objects.create(
            sender=user,
            group=group,
            content=content
        )
        group.save()  # update updated_at timestamp

        avatar_url = None
        if hasattr(user, 'profile') and user.profile.profile_picture:
            avatar_url = user.profile.profile_picture.url

        return {
            'id': msg.id,
            'content': msg.content,
            'timestamp': msg.timestamp.isoformat(),
            'time_display': timezone.localtime(msg.timestamp).strftime('%I:%M %p'),
            'sender_avatar': avatar_url
        }

    @database_sync_to_async
    def set_user_online(self, user, status):
        try:
            profile = user.profile
            profile.is_online = status
            profile.save(update_fields=['is_online', 'last_seen'])
        except Exception:
            pass

    @database_sync_to_async
    def send_group_offline_email_notifications(self, group_id, user, content):
        try:
            group = Group.objects.get(id=group_id)
            notify_offline_group_members(group, user, content)
        except Exception:
            pass
