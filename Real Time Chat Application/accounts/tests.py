from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from accounts.models import UserProfile


class AccountsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='password123',
            first_name='Test',
            last_name='User'
        )

    def test_profile_auto_created_signal(self):
        """Test that UserProfile is automatically created when a User is created."""
        self.assertTrue(hasattr(self.user, 'profile'))
        self.assertEqual(self.user.profile.full_name, 'Test User')

    def test_registration_success(self):
        """Test successful registration with valid inputs."""
        response = self.client.post(reverse('register'), {
            'full_name': 'New Student',
            'username': 'newstudent',
            'email': 'newstudent@example.com',
            'password': 'password123',
            'confirm_password': 'password123'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newstudent').exists())
        new_u = User.objects.get(username='newstudent')
        self.assertEqual(new_u.first_name, 'New')
        self.assertEqual(new_u.last_name, 'Student')

    def test_registration_password_mismatch(self):
        """Test registration failure when passwords do not match."""
        response = self.client.post(reverse('register'), {
            'full_name': 'Mismatch User',
            'username': 'mismatch',
            'email': 'mismatch@example.com',
            'password': 'password123',
            'confirm_password': 'differentpassword'
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='mismatch').exists())

    def test_login_and_logout(self):
        """Test user login authentication and logout status update."""
        login_res = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'password123'
        })
        self.assertEqual(login_res.status_code, 302)
        self.user.profile.refresh_from_db()
        self.assertTrue(self.user.profile.is_online)

        logout_res = self.client.get(reverse('logout'))
        self.assertEqual(logout_res.status_code, 302)
        self.user.profile.refresh_from_db()
        self.assertFalse(self.user.profile.is_online)

    def test_profile_update(self):
        """Test updating profile bio and full name."""
        self.client.login(username='testuser', password='password123')
        response = self.client.post(reverse('profile'), {
            'full_name': 'Updated Name',
            'email': 'updated@example.com',
            'bio': 'Updated bio for testing'
        })
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.last_name, 'Name')
        self.assertEqual(self.user.email, 'updated@example.com')
        self.assertEqual(self.user.profile.bio, 'Updated bio for testing')

    def test_email_notifications_preference_toggle(self):
        """Test default email notification preference and user toggling it off."""
        # Check default is True
        self.assertTrue(self.user.profile.email_notifications)

        self.client.login(username='testuser', password='password123')
        # Submit without email_notifications checkbox to turn it off
        response = self.client.post(reverse('profile'), {
            'full_name': 'Test User',
            'email': 'testuser@example.com',
            'bio': 'My bio'
            # email_notifications omitted -> unchecked -> False
        })
        self.assertEqual(response.status_code, 302)
        self.user.profile.refresh_from_db()
        self.assertFalse(self.user.profile.email_notifications)

        # Submit with email_notifications checked to turn it back on
        response2 = self.client.post(reverse('profile'), {
            'full_name': 'Test User',
            'email': 'testuser@example.com',
            'bio': 'My bio',
            'email_notifications': 'on'
        })
        self.assertEqual(response2.status_code, 302)
        self.user.profile.refresh_from_db()
        self.assertTrue(self.user.profile.email_notifications)

    def test_delete_user_by_admin(self):
        """Test that an admin can delete a registered user."""
        admin_user = User.objects.create_superuser(
            username='site_admin',
            email='admin@example.com',
            password='adminpassword'
        )
        target_user = User.objects.create_user(
            username='user_to_delete',
            email='delete_me@example.com',
            password='password123'
        )

        self.client.login(username='site_admin', password='adminpassword')
        response = self.client.post(reverse('delete_user', kwargs={'user_id': target_user.id}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(User.objects.filter(username='user_to_delete').exists())

    def test_delete_user_by_non_admin_forbidden(self):
        """Test that a regular non-admin user cannot delete any user."""
        other_user = User.objects.create_user(
            username='other_student',
            email='other@example.com',
            password='password123'
        )

        # Log in as normal testuser
        self.client.login(username='testuser', password='password123')
        response = self.client.post(reverse('delete_user', kwargs={'user_id': other_user.id}))
        self.assertEqual(response.status_code, 302)
        # User must still exist
        self.assertTrue(User.objects.filter(username='other_student').exists())
