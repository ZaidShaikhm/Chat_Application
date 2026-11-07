from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from chat.models import Conversation, Group, GroupMembership, Message, Attachment
from chat.notifications import send_offline_email, notify_offline_private_recipient, notify_offline_group_members
from django.core import mail


class ChatTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='password123',
            first_name='Alice',
            last_name='Smith'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='password123',
            first_name='Bob',
            last_name='Jones'
        )
        self.user3 = User.objects.create_user(
            username='user3',
            email='user3@example.com',
            password='password123',
            first_name='Charlie',
            last_name='Brown'
        )

    def test_conversation_get_or_create(self):
        """Test symmetric conversation lookup/creation."""
        c1 = Conversation.get_or_create_conversation(self.user1, self.user2)
        c2 = Conversation.get_or_create_conversation(self.user2, self.user1)
        self.assertEqual(c1.id, c2.id)
        self.assertEqual(c1.get_other_user(self.user1), self.user2)
        self.assertEqual(c1.get_other_user(self.user2), self.user1)

    def test_private_message_and_unread_count(self):
        """Test private message creation, ordering, and unread counts."""
        conv = Conversation.get_or_create_conversation(self.user1, self.user2)
        m1 = Message.objects.create(
            sender=self.user1,
            conversation=conv,
            content='Hello Bob!',
            is_read=False
        )
        self.assertEqual(conv.unread_count_for(self.user2), 1)
        self.assertEqual(conv.unread_count_for(self.user1), 0)
        self.assertEqual(conv.get_last_message().id, m1.id)

        # Logging in as user2 visiting private chat should mark unread as read
        self.client.login(username='user2', password='password123')
        res = self.client.get(reverse('private_chat', kwargs={'username': 'user1'}))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(conv.unread_count_for(self.user2), 0)

    def test_group_creation_and_membership(self):
        """Test creating group, adding members, and group messages."""
        self.client.login(username='user1', password='password123')
        create_res = self.client.post(reverse('create_group'), {
            'name': 'MCA Study Group',
            'description': 'Study collaboration',
            'members': [self.user2.id]
        })
        self.assertEqual(create_res.status_code, 302)
        group = Group.objects.get(name='MCA Study Group')
        self.assertEqual(group.created_by, self.user1)
        self.assertTrue(group.members.filter(id=self.user1.id).exists())
        self.assertTrue(group.members.filter(id=self.user2.id).exists())

        # Test adding member
        add_res = self.client.post(reverse('add_group_member', kwargs={'group_id': group.id}), {
            'members': [self.user3.id]
        })
        self.assertEqual(add_res.status_code, 302)
        self.assertTrue(group.members.filter(id=self.user3.id).exists())

        # Test group message
        g_msg = Message.objects.create(
            sender=self.user1,
            group=group,
            content='Welcome to MCA Study Group!'
        )
        self.assertEqual(group.get_last_message().id, g_msg.id)

    def test_attachment_and_file_upload_api(self):
        """Test file attachment upload via the API endpoint."""
        conv = Conversation.get_or_create_conversation(self.user1, self.user2)
        self.client.login(username='user1', password='password123')

        dummy_image = SimpleUploadedFile(
            "test_image.png",
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82",
            content_type="image/png"
        )

        response = self.client.post(reverse('file_upload'), {
            'conversation_id': conv.id,
            'file': dummy_image,
            'content': 'Test screenshot upload'
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))
        self.assertTrue(data.get('is_image'))

        # Verify in database
        msg = Message.objects.get(id=data['message_id'])
        self.assertEqual(msg.content, 'Test screenshot upload')
        self.assertEqual(msg.attachments.count(), 1)
        att = msg.attachments.first()
        self.assertEqual(att.file_name, 'test_image.png')
        self.assertTrue(att.is_image)

    def test_dashboard_view_and_user_search(self):
        """Test dashboard rendering and user search query."""
        self.client.login(username='user1', password='password123')
        
        # All users
        res = self.client.get(reverse('dashboard'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Bob Jones')
        self.assertContains(res, 'Charlie Brown')

        # Filter by search query
        res_filtered = self.client.get(reverse('dashboard'), {'q': 'Charlie'})
        self.assertEqual(res_filtered.status_code, 200)
        self.assertContains(res_filtered, 'Charlie Brown')
        self.assertNotContains(res_filtered, 'Bob Jones')

    def test_leave_group(self):
        """Test a member leaving a group chat."""
        self.client.login(username='user1', password='password123')
        group = Group.objects.create(name='Leave Test Group', created_by=self.user1)
        GroupMembership.objects.create(group=group, user=self.user1, role='admin')
        GroupMembership.objects.create(group=group, user=self.user2, role='member')

        # User2 logs in and leaves group
        self.client.login(username='user2', password='password123')
        leave_res = self.client.post(reverse('leave_group', kwargs={'group_id': group.id}))
        self.assertEqual(leave_res.status_code, 302)
        self.assertFalse(group.members.filter(id=self.user2.id).exists())
        self.assertTrue(group.members.filter(id=self.user1.id).exists())

        # Attempting to access group chat after leaving should redirect with warning
        chat_res = self.client.get(reverse('group_chat', kwargs={'group_id': group.id}))
        self.assertEqual(chat_res.status_code, 302)

    def test_leave_group_sole_member_deletes_group(self):
        """Test that if the last remaining member leaves, the group is automatically deleted."""
        group = Group.objects.create(name='Sole Group', created_by=self.user1)
        GroupMembership.objects.create(group=group, user=self.user1, role='admin')

        self.client.login(username='user1', password='password123')
        leave_res = self.client.post(reverse('leave_group', kwargs={'group_id': group.id}))
        self.assertEqual(leave_res.status_code, 302)
        self.assertFalse(Group.objects.filter(id=group.id).exists())

    def test_delete_group_by_admin_and_permission_check(self):
        """Test group deletion by admin and rejection for normal members."""
        group = Group.objects.create(name='Delete Test Group', created_by=self.user1)
        GroupMembership.objects.create(group=group, user=self.user1, role='admin')
        GroupMembership.objects.create(group=group, user=self.user2, role='member')

        # User2 (non-admin) tries to delete group -> forbidden
        self.client.login(username='user2', password='password123')
        del_attempt = self.client.post(reverse('delete_group', kwargs={'group_id': group.id}))
        self.assertEqual(del_attempt.status_code, 302)
        self.assertTrue(Group.objects.filter(id=group.id).exists())

        # User1 (admin/creator) deletes group -> successfully deleted
        self.client.login(username='user1', password='password123')
        del_res = self.client.post(reverse('delete_group', kwargs={'group_id': group.id}))
        self.assertEqual(del_res.status_code, 302)
        self.assertFalse(Group.objects.filter(id=group.id).exists())

    def test_join_group_and_remove_member(self):
        """Test joining a group and admin removing a member."""
        group = Group.objects.create(name='Join Test Group', created_by=self.user1)
        GroupMembership.objects.create(group=group, user=self.user1, role='admin')

        # User3 joins group
        self.client.login(username='user3', password='password123')
        join_res = self.client.get(reverse('join_group', kwargs={'group_id': group.id}))
        self.assertEqual(join_res.status_code, 302)
        self.assertTrue(group.members.filter(id=self.user3.id).exists())

        # Admin (User1) removes User3
        self.client.login(username='user1', password='password123')
        remove_res = self.client.post(reverse('remove_group_member', kwargs={
            'group_id': group.id,
            'user_id': self.user3.id
        }))
        self.assertEqual(remove_res.status_code, 302)
        self.assertFalse(group.members.filter(id=self.user3.id).exists())

    def test_offline_email_notification_rules(self):
        """Test offline email logic for online/offline status and preference toggles."""
        # user2 is offline by default (is_online=False) and has email_notifications=True
        self.assertFalse(self.user2.profile.is_online)
        self.assertTrue(self.user2.profile.email_notifications)

        # 1. Sending to offline recipient should return True (notification initiated)
        conv = Conversation.get_or_create_conversation(self.user1, self.user2)
        result = notify_offline_private_recipient(conv, self.user1, 'Hello offline friend!')
        self.assertTrue(result)

        # 2. Sending to online recipient should return False (no notification needed)
        self.user2.profile.is_online = True
        self.user2.profile.save()
        result_online = notify_offline_private_recipient(conv, self.user1, 'Are you there?')
        self.assertFalse(result_online)

        # 3. Sending to offline recipient who disabled notifications should return False
        self.user2.profile.is_online = False
        self.user2.profile.email_notifications = False
        self.user2.profile.save()
        result_disabled = notify_offline_private_recipient(conv, self.user1, 'Notifications disabled test')
        self.assertFalse(result_disabled)

    def test_group_offline_email_notifications(self):
        """Test notifying offline group members when a message is sent."""
        group = Group.objects.create(name='Notice Group', created_by=self.user1)
        GroupMembership.objects.create(group=group, user=self.user1, role='admin')
        GroupMembership.objects.create(group=group, user=self.user2, role='member')
        GroupMembership.objects.create(group=group, user=self.user3, role='member')

        # user2 is offline with notifications ON
        self.user2.profile.is_online = False
        self.user2.profile.email_notifications = True
        self.user2.profile.save()

        # user3 is ONLINE (so should not receive email)
        self.user3.profile.is_online = True
        self.user3.profile.email_notifications = True
        self.user3.profile.save()

        # Sender is user1, only user2 should be notified
        notified_count = notify_offline_group_members(group, self.user1, 'Group update for all')
        self.assertEqual(notified_count, 1)
