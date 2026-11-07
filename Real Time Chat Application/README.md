# Real-Time Chat Application (MCA Academic Project)

A complete, full-stack real-time messaging application developed using **Python**, **Django**, **Django Channels (WebSockets)**, and **SQLite**.

Designed specifically for an **MCA (Master of Computer Applications) Academic Project Demonstration**. The architecture is kept clean, beginner-friendly, and fully modular without unnecessary dependencies (no Node.js, Flask, PHP, or external Firebase servers).

---

## 1. Technology Stack

| Layer | Technologies Used |
|---|---|
| **Backend** | Python 3, Django Framework (5.0+), Django ORM |
| **Real-Time Engine** | Django Channels, Daphne (ASGI Server), InMemoryChannelLayer |
| **Database** | SQLite (`db.sqlite3`) — inspectable with **DB Browser for SQLite** |
| **Frontend** | HTML5, CSS3, Bootstrap 5.3, Bootstrap Icons, JavaScript (ES6+ WebSockets) |
| **Media Handling** | Django Media Storage, Pillow |

---

## 2. Project Directory Structure

```text
Real Time Chat Application/
├── manage.py                          # Django management CLI
├── requirements.txt                   # Project Python dependencies
├── db.sqlite3                         # SQLite database file
├── README.md                          # Complete project documentation & guide
│
├── DjangoChat/                        # Core Project Configuration
│   ├── __init__.py
│   ├── settings.py                    # App configuration, Channels layer, Media settings
│   ├── urls.py                        # Root URL routing & media static serving
│   ├── asgi.py                        # ASGI protocol router (HTTP + WebSockets)
│   └── wsgi.py                        # WSGI server entry point
│
├── accounts/                          # Authentication & User Profiles App
│   ├── models.py                      # UserProfile model with signals
│   ├── views.py                       # Register, Login, Logout, Profile update views
│   ├── forms.py                       # UserRegistrationForm, UserLoginForm, UserProfileUpdateForm
│   ├── urls.py                        # /accounts/ authentication routes
│   ├── admin.py                       # Admin site registration for UserProfile
│   └── tests.py                       # Unit & integration tests for accounts
│
├── chat/                              # Real-Time Messaging App
│   ├── models.py                      # Conversation, Group, GroupMembership, Message, Attachment
│   ├── views.py                       # Dashboard, Private chat, Group chat, File upload API
│   ├── consumers.py                   # PrivateChatConsumer & GroupChatConsumer (WebSockets)
│   ├── routing.py                     # WebSocket URL patterns (/ws/chat/, /ws/group/)
│   ├── urls.py                        # Chat views and AJAX API endpoints
│   ├── admin.py                       # Django Admin configuration with inlines
│   ├── tests.py                       # Unit & integration tests for chat & WebSockets
│   └── management/
│       └── commands/
│           └── seed_data.py           # Populates demonstration accounts, groups, and chats
│
├── templates/                         # HTML5 Django Templates (Bootstrap 5)
│   ├── base.html                      # Main layout, navbar, dual-theme switcher, flash alerts
│   ├── home.html                      # Project landing page with features overview
│   ├── register.html                  # User registration page
│   ├── login.html                     # User authentication page
│   ├── dashboard.html                 # Dashboard, registered user directory, search, recent chats
│   ├── chat.html                      # 1-on-1 private real-time chat interface
│   ├── group_chat.html                # Multi-user group chat room interface
│   └── profile.html                   # User profile editing & SQLite record viewer
│
├── static/                            # Static Assets
│   ├── css/
│   │   └── style.css                  # Custom styling with dual Light & Dark themes
│   └── js/
│       └── chat.js                    # ChatClient WebSocket engine, typing indicators, audio beeps
│
└── media/                             # Uploaded Content
    ├── profiles/                      # User profile avatars
    ├── attachments/                   # Chat file and image attachments
    └── group_avatars/                 # Group profile pictures
```

---

## 3. Database Design & Tables (SQLite)

The application stores all relational data in SQLite (`db.sqlite3`). You can inspect and query all tables using **DB Browser for SQLite**:

1. **`auth_user`**: Standard Django authentication table (stores user ID, username, password hash, email, first name, last name, date joined).
2. **`accounts_userprofile`**: Extended user details linked One-to-One with `auth_user` (`bio`, `profile_picture`, `is_online`, `last_seen`).
3. **`chat_conversation`**: Tracks private one-to-one chats between two users (`user1_id`, `user2_id`, `created_at`, `updated_at`).
4. **`chat_group`**: Chat rooms created by users (`name`, `description`, `avatar`, `created_by_id`, `created_at`, `updated_at`).
5. **`chat_groupmembership`**: Maps users to groups with permission roles (`group_id`, `user_id`, `role`, `joined_at`).
6. **`chat_message`**: Chat messages for both private and group conversations (`sender_id`, `conversation_id`, `group_id`, `content`, `timestamp`, `is_read`).
7. **`chat_attachment`**: Files, images, and documents shared inside messages (`message_id`, `file`, `file_name`, `file_type`, `file_size`, `uploaded_at`).

---

## 4. Key Features Implemented

1. **User Authentication & Profiles**:
   - Secure registration with full name, username, email, and password validation.
   - Login, logout with automatic online/offline status tracking.
   - Profile photo upload and status bio customization.
   - Flash feedback messages for every action.

2. **User Dashboard & Directory**:
   - Live list of all registered users with real-time online/offline badges.
   - Live search bar to search registered students by name, username, or email.
   - Recent private chats with unread message badges.
   - Quick group room shortcuts.
   - **Admin-Only User Deletion**: System administrators have exclusive authority to delete registered users directly from the dashboard directory with confirmation modals. Regular users cannot access or view deletion controls.

3. **1-on-1 Real-Time Private Chat**:
   - Instant message transmission via WebSockets without page reload.
   - Visual distinction between sent (right) and received (left) message bubbles.
   - Message timestamps and read receipts (single check `✓` to double blue check `✓✓`).
   - SQLite conversation history loaded on entrance.
   - Real-time typing indicators ("*User is typing...*").

4. **Multi-User Group Chat & Group Management**:
   - Create custom groups with group name, description, and avatar.
   - Select multiple registered users to join upon creation or add later via modal.
   - Group messages broadcast in real time to all connected members with sender names and avatars.
   - View members modal listing all group participants and admin badges.
   - **Leave Group**: Any member can leave the group with instant real-time notification to remaining members.
   - **Delete Group**: Group creators and administrators can permanently delete the group and its message history from SQLite.
   - **Remove Members & Join**: Admins can remove members, and users can join available groups from the dashboard.

5. **Attachment Sharing**:
   - Direct image and file upload in both private and group chats.
   - File attachment card with live preview, download button, and file size metadata.
   - Automatic image thumbnail rendering.

6. **Offline Email Notifications (Gmail SMTP & Console Preview)**:
   - When a registered user is offline and receives a new private message, group message, or file attachment, an automated notification is sent to their registered Gmail account.
   - Contains sender name, chat room name, message preview, and Indian Standard Time (IST) timestamp.
   - Runs in a non-blocking background thread so real-time WebSocket speed is never impacted.
   - User-configurable preference toggle in **Profile Settings** to enable/disable offline email alerts.
   - Dual-mode delivery:
     - **Console Mode (Default)**: Prints formatted emails directly to the server terminal — ideal for local college viva evaluation without needing external internet access.
     - **Live Gmail SMTP Mode**: Enter your Gmail and Google App Password to deliver real emails to actual Gmail inboxes!

7. **Modern UI & Dual Themes**:
   - Built with Bootstrap 5 and custom CSS.
   - Light and Dark mode toggle with preference saved in `localStorage`.
   - Subtle audio notification chime on receiving incoming messages.
   - Fully responsive for mobile and desktop screens.

---

## 5. Installation and Setup Instructions

### Prerequisites
- Python 3.10 or higher installed on your system.

### Step 1: Open Terminal in Project Directory
```powershell
cd "c:\Users\ASUS\Documents\Real Time Chat Application"
```

### Step 2: Activate the Virtual Environment
On Windows PowerShell:
```powershell
.\venv\Scripts\Activate.ps1
```
*(Or Command Prompt: `venv\Scripts\activate.bat`)*

### Step 3: Install Required Dependencies
```powershell
pip install -r requirements.txt
```

### Step 4: Apply Database Migrations
Create the SQLite tables in `db.sqlite3`:
```powershell
python manage.py makemigrations
python manage.py migrate
```

### Step 5: Seed Demonstration Data (Optional but Recommended)
Populates demo users, conversations, and groups for project presentation:
```powershell
python manage.py seed_data
```

### Step 6: Start the Real-Time Development Server
Run the ASGI server (Daphne runs automatically via Django):
```powershell
python manage.py runserver
```

Open your browser and navigate to:
```text
http://127.0.0.1:8000/
```

---

## 6. Pre-seeded Demo Accounts

| Username | Password | Role | Description |
|---|---|---|---|
| `admin` | `admin123` | Superuser / Admin | Full Django Admin access (`/admin/`) |
| `rahul_sharma` | `password123` | Student User | MCA 4th Sem, Group Admin |
| `priya_patel` | `password123` | Student User | Full Stack Developer |
| `amit_verma` | `password123` | Student User | Backend Architect |
| `sneha_reddy` | `password123` | Student User | UI/UX Designer |

---

## 7. How to Demonstrate in an Academic Viva

1. **Demonstrate 1-on-1 Real-Time Chatting**:
   - Open two different browsers (e.g. Chrome and Edge) or one standard window and one Incognito window.
   - Log into Browser 1 as `rahul_sharma` and Browser 2 as `priya_patel`.
   - In Browser 1, open chat with `priya_patel`. In Browser 2, open chat with `rahul_sharma`.
   - Notice the connection badge turns green (`Connected`).
   - Start typing in Browser 1: observe the live typing indicator in Browser 2.
   - Send a message: observe it appear instantly in Browser 2 without refreshing the page!

2. **Demonstrate Group Messaging**:
   - In both browsers, navigate to **Groups** and open **MCA Project Team 2026**.
   - Send a group message: all connected members receive the message with sender attribution and timestamp.

3. **Demonstrate File & Image Sharing**:
   - Click the paperclip icon in the message bar, select an image or document, and hit send.
   - Both browsers show the attachment card with a preview or download link.

4. **Demonstrate Offline Gmail Notifications**:
   - Log out of Browser 2 (or leave user offline).
   - In Browser 1, send a direct message or group message to the offline user.
   - Look at the terminal running `runserver`: see the complete formatted email notification printed instantly with subject, sender, timestamp, and message preview!
   - (Optional) Set `EMAIL_HOST_USER` and `EMAIL_HOST_PASSWORD` in your environment or `settings.py` with a Google App Password to deliver live emails directly to your Gmail inbox!

5. **Demonstrate SQLite Database Records in DB Browser for SQLite**:
   - Open **DB Browser for SQLite**.
   - Click **Open Database** and select `db.sqlite3` from the project directory.
   - Go to the **Browse Data** tab:
     - Select table `auth_user` to show registered student accounts.
     - Select table `chat_message` to show every message saved with its sender and timestamp.
     - Select table `chat_attachment` to show file paths and metadata.
     - Select table `accounts_userprofile` to show `is_online` status updates and `email_notifications` preference.

6. **Run the Automated Test Suite**:
   ```powershell
   python manage.py test
   ```
   Runs 19 comprehensive unit and integration tests verifying registration, login, admin user deletion, conversations, groups, attachments, search, and offline email notifications.

