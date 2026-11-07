from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from chat.models import Conversation, Group, GroupMembership, Message
from accounts.models import UserProfile


class Command(BaseCommand):
    help = 'Seeds initial sample data for MCA Project Demonstration'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Seeding MCA Chat demonstration data...'))

        # 1. Create Superuser admin
        if not User.objects.filter(username='admin').exists():
            admin_user = User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
            admin_user.first_name = 'System'
            admin_user.last_name = 'Administrator'
            admin_user.save()
            admin_profile, _ = UserProfile.objects.get_or_create(user=admin_user)
            admin_profile.bio = 'System Admin & Project Overseer'
            admin_profile.save()
            self.stdout.write(self.style.SUCCESS('Created superuser: admin (password: admin123)'))

        # 2. Create Sample Student Users
        sample_users = [
            {
                'username': 'rahul_sharma',
                'first_name': 'Rahul',
                'last_name': 'Sharma',
                'email': 'rahul@example.com',
                'bio': 'MCA 4th Sem | Python & Django Enthusiast'
            },
            {
                'username': 'priya_patel',
                'first_name': 'Priya',
                'last_name': 'Patel',
                'email': 'priya@example.com',
                'bio': 'Full Stack Developer | Exploring WebSockets'
            },
            {
                'username': 'amit_verma',
                'first_name': 'Amit',
                'last_name': 'Verma',
                'email': 'amit@example.com',
                'bio': 'Backend Architect | SQLite & PostgreSQL'
            },
            {
                'username': 'sneha_reddy',
                'first_name': 'Sneha',
                'last_name': 'Reddy',
                'email': 'sneha@example.com',
                'bio': 'UI/UX Designer & Frontend Developer'
            }
        ]

        created_user_objs = {}
        for udata in sample_users:
            user, created = User.objects.get_or_create(username=udata['username'])
            user.first_name = udata['first_name']
            user.last_name = udata['last_name']
            user.email = udata['email']
            user.set_password('password123')
            user.save()

            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.bio = udata['bio']
            profile.email_notifications = True
            profile.save()
            created_user_objs[udata['username']] = user
            self.stdout.write(self.style.SUCCESS(f"Configured demo user: {udata['username']} (password: password123)"))

        # 3. Create Sample 1-on-1 Conversation
        rahul = created_user_objs['rahul_sharma']
        priya = created_user_objs['priya_patel']
        conv = Conversation.get_or_create_conversation(rahul, priya)

        if not conv.messages.exists():
            Message.objects.create(
                sender=rahul,
                conversation=conv,
                content="Hey Priya! Have you checked out the Django Channels WebSocket implementation?",
                is_read=True
            )
            Message.objects.create(
                sender=priya,
                conversation=conv,
                content="Yes Rahul! Messages are delivered instantly without page reload. It's working great!",
                is_read=True
            )
            Message.objects.create(
                sender=rahul,
                conversation=conv,
                content="Awesome! SQLite also stores all conversation records accurately.",
                is_read=False
            )
            conv.save()
            self.stdout.write(self.style.SUCCESS("Created sample private conversation between Rahul and Priya."))

        # 4. Create Sample Group
        group, g_created = Group.objects.get_or_create(
            name="MCA Project Team 2026",
            defaults={
                'description': 'Official collaboration channel for MCA Real-Time Chat Project discussion.',
                'created_by': rahul
            }
        )

        # Add Members
        GroupMembership.objects.get_or_create(group=group, user=rahul, defaults={'role': 'admin'})
        GroupMembership.objects.get_or_create(group=group, user=priya, defaults={'role': 'member'})
        GroupMembership.objects.get_or_create(group=group, user=created_user_objs['amit_verma'], defaults={'role': 'member'})
        GroupMembership.objects.get_or_create(group=group, user=created_user_objs['sneha_reddy'], defaults={'role': 'member'})

        if not group.messages.exists():
            Message.objects.create(
                sender=rahul,
                group=group,
                content="Welcome everyone to our MCA Project Discussion group!"
            )
            Message.objects.create(
                sender=created_user_objs['amit_verma'],
                group=group,
                content="Glad to be here! The real-time synchronization is seamless."
            )
            Message.objects.create(
                sender=created_user_objs['sneha_reddy'],
                group=group,
                content="The dark and light mode UI looks very professional!"
            )
            group.save()
            self.stdout.write(self.style.SUCCESS("Created sample group 'MCA Project Team 2026' with messages."))

        self.stdout.write(self.style.SUCCESS("\nDemonstration data seeding complete!"))
        self.stdout.write(self.style.SUCCESS("Demo credentials: username: rahul_sharma | password: password123"))
        self.stdout.write(self.style.SUCCESS("Admin credentials: username: admin | password: admin123\n"))
