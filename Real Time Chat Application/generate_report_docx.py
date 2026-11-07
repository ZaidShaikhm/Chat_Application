import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import qn, nsdecls


def set_cell_background(cell, hex_color):
    shading_elm = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    cell._tc.get_or_add_tcPr().append(shading_elm)


def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)


def add_table_row(table, col_data, is_header=False, bg_color=None):
    row = table.add_row()
    for i, text in enumerate(col_data):
        cell = row.cells[i]
        cell.text = text
        set_cell_margins(cell, top=120, bottom=120, left=160, right=160)
        p = cell.paragraphs[0]
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.space_before = Pt(2)
        if is_header:
            p.runs[0].font.bold = True
            p.runs[0].font.color.rgb = RGBColor(255, 255, 255)
            p.runs[0].font.size = Pt(10)
            set_cell_background(cell, "2B3A67")
        else:
            p.runs[0].font.size = Pt(9.5)
            if bg_color:
                set_cell_background(cell, bg_color)
    return row


def create_report():
    doc = docx.Document()

    # Set page margins (1 inch all sides)
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)

    # Styles
    primary_color = RGBColor(43, 58, 103)      # Navy #2B3A67
    secondary_color = RGBColor(79, 70, 229)    # Indigo #4F46E5
    text_color = RGBColor(30, 41, 59)          # Slate dark #1E293B

    normal_style = doc.styles['Normal']
    normal_style.font.name = 'Calibri'
    normal_style.font.size = Pt(11)
    normal_style.font.color.rgb = text_color
    normal_style.paragraph_format.line_spacing = 1.2
    normal_style.paragraph_format.space_after = Pt(6)

    # ==================== COVER PAGE ====================
    title_p = doc.add_paragraph()
    title_p.paragraph_format.space_before = Pt(72)
    title_p.paragraph_format.space_after = Pt(12)
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_sub = title_p.add_run("MCA ACADEMIC PROJECT REPORT\n")
    run_sub.font.size = Pt(14)
    run_sub.font.bold = True
    run_sub.font.color.rgb = secondary_color

    run_title = title_p.add_run("REAL-TIME CHAT APPLICATION\nUSING PYTHON & DJANGO CHANNELS")
    run_title.font.size = Pt(24)
    run_title.font.bold = True
    run_title.font.color.rgb = primary_color

    desc_p = doc.add_paragraph()
    desc_p.paragraph_format.space_before = Pt(18)
    desc_p.paragraph_format.space_after = Pt(72)
    desc_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    desc_run = desc_p.add_run("A Full-Stack Real-Time Messaging Platform with WebSockets, SQLite Relational Database, and Responsive Dual Themes")
    desc_run.font.size = Pt(12)
    desc_run.font.italic = True
    desc_run.font.color.rgb = RGBColor(100, 116, 139)

    info_p = doc.add_paragraph()
    info_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    info_p.paragraph_format.space_before = Pt(120)
    info_p.paragraph_format.space_after = Pt(4)
    r1 = info_p.add_run("Master of Computer Applications (MCA)\n")
    r1.font.bold = True
    r1.font.size = Pt(13)
    r1.font.color.rgb = primary_color
    r2 = info_p.add_run("Department of Computer Science & Applications\nAcademic Year 2026")
    r2.font.size = Pt(11)
    r2.font.color.rgb = text_color

    doc.add_page_break()

    # Helper function for headings
    def add_h1(text):
        h = doc.add_paragraph()
        h.paragraph_format.space_before = Pt(18)
        h.paragraph_format.space_after = Pt(8)
        h.paragraph_format.keep_with_next = True
        r = h.add_run(text)
        r.font.name = 'Calibri'
        r.font.size = Pt(16)
        r.font.bold = True
        r.font.color.rgb = primary_color
        return h

    def add_h2(text):
        h = doc.add_paragraph()
        h.paragraph_format.space_before = Pt(14)
        h.paragraph_format.space_after = Pt(6)
        h.paragraph_format.keep_with_next = True
        r = h.add_run(text)
        r.font.name = 'Calibri'
        r.font.size = Pt(13)
        r.font.bold = True
        r.font.color.rgb = secondary_color
        return h

    def add_h3(text):
        h = doc.add_paragraph()
        h.paragraph_format.space_before = Pt(10)
        h.paragraph_format.space_after = Pt(4)
        h.paragraph_format.keep_with_next = True
        r = h.add_run(text)
        r.font.name = 'Calibri'
        r.font.size = Pt(11.5)
        r.font.bold = True
        r.font.color.rgb = text_color
        return h

    # ==================== TABLE OF CONTENTS ====================
    add_h1("TABLE OF CONTENTS")
    toc_items = [
        ("1. Project Title & Abstract", "3"),
        ("2. Problem Statement & Project Objectives", "4"),
        ("3. System Architecture & Real-Time Data Flow", "5"),
        ("4. Technology Stack & Specifications", "6"),
        ("5. Database Design & Relational Schema (SQLite)", "7"),
        ("6. Module-by-Module Functional Specification", "9"),
        ("7. Group Management: Leave & Delete System", "11"),
        ("8. Security, Data Validation & Business Logic", "12"),
        ("9. Quality Assurance & Automated Test Suite", "13"),
        ("10. Installation, Configuration & Execution Manual", "14"),
        ("11. Pre-Seeded Demonstration Accounts & Viva Guide", "15"),
        ("12. Conclusion & Future Enhancements", "16"),
    ]
    toc_table = doc.add_table(rows=0, cols=2)
    toc_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    toc_table.columns[0].width = Inches(5.2)
    toc_table.columns[1].width = Inches(1.3)
    add_table_row(toc_table, ["Section / Topic", "Page"], is_header=True)
    for title, pg in toc_items:
        add_table_row(toc_table, [title, pg])

    doc.add_page_break()

    # ==================== SECTION 1 ====================
    add_h1("1. PROJECT TITLE & ABSTRACT")
    add_h2("1.1 Project Title")
    p = doc.add_paragraph()
    p.add_run("DjangoChat: A Real-Time Communication Platform using Python, Django Channels, WebSockets, and SQLite.")

    add_h2("1.2 Project Abstract")
    p = doc.add_paragraph(
        "In modern web applications, real-time bidirectional communication is essential for messaging, collaboration, "
        "and interactive user experiences. Traditional HTTP architectures rely on stateless request-response cycles "
        "(such as polling or long-polling), which create noticeable latency, redundant network bandwidth consumption, "
        "and server connection bottlenecks."
    )
    p = doc.add_paragraph(
        "This project presents a comprehensive, full-stack Real-Time Chat Application specifically architected for an "
        "MCA Academic Project Demonstration. Built with Python 3, Django, Django Channels, and the Daphne ASGI server, "
        "the application establishes full-duplex WebSocket connections (ws://) for instantaneous message transmission without "
        "requiring page refreshes. Data persistence is guaranteed through a normalized SQLite database (db.sqlite3), "
        "which can be visually managed and inspected through DB Browser for SQLite. The user interface is built with "
        "HTML5, CSS3, Bootstrap 5.3, and vanilla JavaScript, offering private 1-on-1 chats, dynamic multi-user group chat rooms, "
        "live typing indicators, online/offline presence tracking, read receipts, multimedia attachments, and Light/Dark theme switching."
    )

    # ==================== SECTION 2 ====================
    add_h1("2. PROBLEM STATEMENT & PROJECT OBJECTIVES")
    add_h2("2.1 Problem Statement")
    p = doc.add_paragraph(
        "Standard web applications struggle to support low-latency communication because HTTP is fundamentally a "
        "unidirectional, request-driven protocol. Implementing chat features using standard Django views and periodic Ajax polling "
        "leads to severe drawbacks: excessive server resource utilization, database query spikes, delayed message delivery, "
        "and a degraded user experience. There is a strong academic and practical need to demonstrate how asynchronous ASGI protocols "
        "and WebSockets can be cleanly unified with traditional Django MVC architecture without relying on external third-party services."
    )

    add_h2("2.2 Project Objectives")
    bullets = [
        ("Zero-Latency Message Delivery: ", "Utilize persistent WebSocket connections to deliver text and media in real time."),
        ("Strict Language Compliance: ", "Implement the entire backend exclusively in Python and Django without Node.js, Flask, PHP, or Firebase."),
        ("Relational SQLite Persistence: ", "Ensure all user accounts, messages, attachments, and memberships are properly structured in SQLite."),
        ("Comprehensive Group Lifecycle: ", "Provide full group chat functionality, including group creation, adding members, leaving groups, and admin group deletion."),
        ("Independent Local Execution: ", "Employ Channels' InMemoryChannelLayer so that the project runs seamlessly out-of-the-box on local workstations without demanding external Redis instances."),
        ("Professional User Experience: ", "Design an attractive, responsive UI featuring dual Light/Dark modes, Indian Standard Time timestamps, and audio notification chimes.")
    ]
    for b_title, b_desc in bullets:
        bp = doc.add_paragraph(style='List Bullet')
        r1 = bp.add_run(b_title)
        r1.bold = True
        bp.add_run(b_desc)

    # ==================== SECTION 3 ====================
    add_h1("3. SYSTEM ARCHITECTURE & REAL-TIME DATA FLOW")
    add_h2("3.1 Asynchronous Server Gateway Interface (ASGI)")
    p = doc.add_paragraph(
        "Django was traditionally built on WSGI (Web Server Gateway Interface), which is synchronously tied to a single "
        "request and response. Django Channels upgrades this architecture to ASGI (Asynchronous Server Gateway Interface). "
        "Under ASGI, Django handles standard HTTP web pages while simultaneously holding thousands of persistent WebSocket connections open."
    )

    add_h2("3.2 Real-Time Message Transmission Flow")
    steps = [
        "1. Handshake: The browser opens a WebSocket connection to ws://localhost:8000/ws/chat/<id>/ or /ws/group/<id>/.",
        "2. Authentication & Authorization: Daphne and Channels' AuthMiddlewareStack authenticate the session cookie and ensure the user is an active participant.",
        "3. Channel Group Join: The consumer binds the socket connection to a specific channel layer group (e.g., chat_12 or group_5).",
        "4. Message Send: When a user submits text, JavaScript sends a JSON payload: {'type': 'chat_message', 'message': '...'}.",
        "5. Asynchronous Storage: The consumer executes a database_sync_to_async worker that persists the Message in SQLite.",
        "6. Broadcast: The channel layer fans out a chat_message_forward event to all active connections in the room.",
        "7. Dynamic DOM Rendering: JavaScript receives the JSON event, plays an audio chime, and renders the new chat bubble immediately."
    ]
    for step in steps:
        sp = doc.add_paragraph()
        sp.paragraph_format.left_indent = Inches(0.2)
        sp.paragraph_format.space_after = Pt(3)
        sp.add_run(step)

    # ==================== SECTION 4 ====================
    add_h1("4. TECHNOLOGY STACK & SPECIFICATIONS")
    tech_table = doc.add_table(rows=0, cols=3)
    tech_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    tech_table.columns[0].width = Inches(1.8)
    tech_table.columns[1].width = Inches(2.2)
    tech_table.columns[2].width = Inches(2.5)
    add_table_row(tech_table, ["Layer / Component", "Technology Used", "Role in This System"], is_header=True)
    tech_data = [
        ("Backend Language", "Python 3.10+ / 3.14", "Core application programming, async coroutines"),
        ("Web Framework", "Django 5.0+ / 6.1", "MVC/MVT routing, authentication, ORM database logic"),
        ("Real-Time Protocol", "Django Channels 4.3", "WebSocket protocol routing and room channel layers"),
        ("ASGI Web Server", "Daphne 4.2", "Twisted-based asynchronous HTTP & WebSocket server"),
        ("Channel Layer", "InMemoryChannelLayer", "In-process memory broker for WebSocket broadcasts"),
        ("Database", "SQLite (db.sqlite3)", "Relational persistent storage, zero-configuration"),
        ("Database Tool", "DB Browser for SQLite", "Inspection of tables, records, schemas, and queries"),
        ("Frontend Structure", "HTML5 & Django Templates", "Semantic templates with template tags and inheritance"),
        ("Frontend Styling", "CSS3 & Bootstrap 5.3", "Responsive layout, card components, Light/Dark modes"),
        ("Client Scripting", "Vanilla JavaScript (ES6+)", "Native WebSocket client, DOM updates, Audio API"),
        ("Email Notification Engine", "Gmail SMTP / Console Backend", "Automated email alerts to offline users via TLS port 587"),
        ("Image Processing", "Pillow 10.0+", "Validation and processing of uploaded images/avatars")
    ]
    for i, row in enumerate(tech_data):
        bg = "F8FAFC" if i % 2 == 1 else "FFFFFF"
        add_table_row(tech_table, [row[0], row[1], row[2]], bg_color=bg)

    # ==================== SECTION 5 ====================
    add_h1("5. DATABASE DESIGN & RELATIONAL SCHEMA (SQLITE)")
    p = doc.add_paragraph(
        "All data is normalized across 7 relational tables in SQLite. The database schema enforces referential "
        "integrity through foreign keys and cascading deletion rules (on_delete=models.CASCADE):"
    )

    models_info = [
        ("auth_user (Django Core User)", "Stores system credentials, including username, encrypted password, email, first name, last name, and date joined."),
        ("accounts_userprofile (User Profile)", "Linked One-to-One with auth_user. Stores user biography, profile picture avatar, is_online status boolean, email_notifications preference boolean, and last_seen timestamp."),
        ("chat_conversation (Private 1-on-1 Chat)", "Represents private threads between two users (user1 and user2). Enforces a unique constraint pair to ensure single conversation threads regardless of who initiated."),
        ("chat_group (Group Chat Room)", "Stores group chat rooms, including group name, description, avatar photo, created_by user reference, and timestamps."),
        ("chat_groupmembership (Group Member & Role)", "Join table connecting users to groups. Tracks user role ('admin' or 'member') and joined_at timestamp."),
        ("chat_message (Chat Message)", "Stores messages for both private conversations and group channels. Contains content text, timestamp (IST), sender reference, and is_read boolean."),
        ("chat_attachment (File & Media Attachment)", "Linked One-to-Many with chat_message. Tracks uploaded files, file_name, MIME file_type, file_size string, and upload date.")
    ]
    for m_name, m_desc in models_info:
        mp = doc.add_paragraph(style='List Bullet')
        r = mp.add_run(m_name + ": ")
        r.bold = True
        mp.add_run(m_desc)

    # ==================== SECTION 6 ====================
    add_h1("6. MODULE-BY-MODULE FUNCTIONAL SPECIFICATION")
    add_h2("6.1 Authentication & User Profile Module (accounts)")
    p = doc.add_paragraph(
        "Manages user registration, authentication, sessions, and profile customization. Registration validates username "
        "uniqueness, valid email formats, and password confirmation. UserProfile records are automatically instantiated via Django "
        "post_save signals. Login/logout actions dynamically update the is_online status."
    )

    add_h2("6.2 User Dashboard & Directory Module (chat)")
    p = doc.add_paragraph(
        "Serves as the main operational hub. Displays current user bio, recent conversations with unread counter badges, "
        "active group rooms, and a directory of all registered users with real-time online/offline indicators. A live search bar "
        "enables instantaneous filtering of users by full name, username, or email."
    )

    add_h2("6.3 Private 1-on-1 Messaging Module (chat)")
    p = doc.add_paragraph(
        "Allows direct communication between any two registered users. Employs PrivateChatConsumer over /ws/chat/<conv_id>/. "
        "Visually differentiates sent messages (right-aligned, indigo gradient) from received messages (left-aligned, white/gray). "
        "Loads past conversation history from SQLite upon connection and marks incoming messages as read, triggering instant "
        "double blue checkmark (✓✓) read receipts."
    )

    add_h2("6.4 Multimedia & File Sharing Module (chat)")
    p = doc.add_paragraph(
        "Users can upload images, screenshots, PDFs, and documents through an asynchronous multipart API (/api/upload/). "
        "Files are stored in the media/ directory, and the file metadata is stored in SQLite. Images render with inline thumbnails, "
        "while documents feature downloadable cards displaying file name and size."
    )

    add_h2("6.5 Real-Time Polish & UI Enhancements")
    p = doc.add_paragraph(
        "Features real-time typing indicators ('<User> is typing...'), subtle Web Audio API chimes upon message receipt, "
        "Indian Standard Time (Asia/Kolkata) timestamps, and responsive CSS with instant Light/Dark mode toggling."
    )

    add_h2("6.6 Offline Email Notification Module (chat.notifications)")
    p = doc.add_paragraph(
        "Automatically detects when a recipient user is offline (is_online=False). When any direct message, group message, or "
        "file attachment is received, an email notification is dispatched to their registered Gmail address. The email includes "
        "the sender's name, chat channel, IST timestamp, and a formatted message preview. Dispatches run in asynchronous "
        "daemon threads to preserve sub-millisecond WebSocket response times. Users can easily toggle notifications in their Profile Settings."
    )

    # ==================== SECTION 7 ====================
    add_h1("7. GROUP MANAGEMENT: LEAVE & DELETE SYSTEM")
    p = doc.add_paragraph(
        "Group communication includes a complete lifecycle management system designed for robust administration:"
    )

    add_h2("7.1 Leave Group Functionality (/group/<id>/leave/)")
    bullets_leave = [
        ("Membership Revocation: ", "Any member can leave a group chat at any time. Their GroupMembership record is deleted from SQLite."),
        ("Admin Role Transfer: ", "If the departing member was the group creator or sole admin, admin privileges are automatically transferred to the next oldest member."),
        ("Automatic Group Cleanup: ", "If the departing user was the last remaining member in the group, the empty group is automatically deleted from the database."),
        ("Real-Time Broadcast: ", "A system message ('User has left the group') is saved in SQLite and broadcast via WebSockets to remaining active members.")
    ]
    for b_title, b_desc in bullets_leave:
        bp = doc.add_paragraph(style='List Bullet')
        r1 = bp.add_run(b_title)
        r1.bold = True
        bp.add_run(b_desc)

    add_h2("7.2 Delete Group Functionality (/group/<id>/delete/)")
    bullets_del = [
        ("Role Authorization: ", "Restricted exclusively to group creators and group administrators."),
        ("Cascading Deletion: ", "Permanently removes the group record; SQLite cascades and removes all associated memberships, messages, and attachments."),
        ("Confirmation Safety: ", "A Bootstrap modal warns the admin that the action is irreversible before executing the POST request.")
    ]
    for b_title, b_desc in bullets_del:
        bp = doc.add_paragraph(style='List Bullet')
        r1 = bp.add_run(b_title)
        r1.bold = True
        bp.add_run(b_desc)

    add_h2("7.3 Join & Member Removal System")
    p = doc.add_paragraph(
        "Users can browse available open groups and join with one click from the dashboard. Group administrators can also "
        "remove specific members through the interactive 'View Members' modal."
    )

    # ==================== SECTION 8 ====================
    add_h1("8. SECURITY, DATA VALIDATION & BUSINESS LOGIC")
    sec_points = [
        ("Cryptographic Password Hashing: ", "Passwords are encrypted using PBKDF2 with SHA-256 and unique salts. Plaintext passwords are never saved."),
        ("CSRF Token Protection: ", "Every form and file upload request enforces Django's CsrfViewMiddleware to protect against Cross-Site Request Forgery."),
        ("Session-Aware WebSocket Auth: ", "Channels' AuthMiddlewareStack validates the session cookie during the WebSocket handshake."),
        ("Access Authorization: ", "Users cannot message themselves, cannot delete groups they do not administer, and cannot access group chats unless they are valid members."),
        ("Admin-Only User Deletion: ", "Only system administrators (superuser/staff) are authorized to delete registered users. Non-admin users are strictly forbidden."),
        ("SQL Injection Mitigation: ", "All database transactions use the parameterized Django ORM (select_related, prefetch_related, Q filters).")
    ]
    for s_title, s_desc in sec_points:
        sp = doc.add_paragraph(style='List Bullet')
        r = sp.add_run(s_title)
        r.bold = True
        sp.add_run(s_desc)

    # ==================== SECTION 9 ====================
    add_h1("9. QUALITY ASSURANCE & AUTOMATED TEST SUITE")
    p = doc.add_paragraph(
        "The project includes an automated test suite with 19 unit and integration tests covering accounts and chat apps. "
        "All tests pass successfully with 0 errors:"
    )

    test_table = doc.add_table(rows=0, cols=2)
    tech_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    test_table.columns[0].width = Inches(3.2)
    test_table.columns[1].width = Inches(3.3)
    add_table_row(test_table, ["Test Method Name", "Verified Business Functionality"], is_header=True)
    tests_data = [
        ("test_profile_auto_created_signal", "Verifies UserProfile creation signal on new User creation"),
        ("test_registration_success", "Tests user registration with valid data and full name splitting"),
        ("test_registration_password_mismatch", "Validates rejection when password and confirm_password differ"),
        ("test_login_and_logout", "Tests authentication, session creation, and is_online toggling"),
        ("test_profile_update", "Verifies editing full name, email, and biography in SQLite"),
        ("test_email_notifications_preference_toggle", "Tests default email notification preference and user toggling it off/on"),
        ("test_delete_user_by_admin", "Validates that only administrators can permanently delete registered users"),
        ("test_delete_user_by_non_admin_forbidden", "Ensures normal users are strictly forbidden from deleting users"),
        ("test_conversation_get_or_create", "Tests symmetric lookup of 1-on-1 private conversations"),
        ("test_private_message_and_unread_count", "Validates message creation, unread counts, and read status"),
        ("test_group_creation_and_membership", "Verifies group creation with creator as admin and member addition"),
        ("test_attachment_and_file_upload_api", "Tests binary file upload endpoint and image classification"),
        ("test_dashboard_view_and_user_search", "Tests dashboard rendering and user search query filtering"),
        ("test_leave_group", "Tests member leaving group and membership removal"),
        ("test_leave_group_sole_member_deletes_group", "Verifies automatic deletion of empty groups"),
        ("test_delete_group_by_admin_and_permission_check", "Tests group deletion by admin and rejection for non-admins"),
        ("test_join_group_and_remove_member", "Tests user joining a group and admin removing a member"),
        ("test_offline_email_notification_rules", "Verifies offline notification triggering rules (offline status and preference)"),
        ("test_group_offline_email_notifications", "Validates group messages notify only offline members with alerts enabled")
    ]
    for i, row in enumerate(tests_data):
        bg = "F8FAFC" if i % 2 == 1 else "FFFFFF"
        add_table_row(test_table, [row[0], row[1]], bg_color=bg)

    # ==================== SECTION 10 ====================
    add_h1("10. INSTALLATION, CONFIGURATION & EXECUTION MANUAL")
    add_h2("10.1 System Prerequisites")
    p = doc.add_paragraph("Python 3.10 or higher installed. Virtual environment located in the project root directory.")

    add_h2("10.2 Step-by-Step Terminal Execution Commands")
    cmd_steps = [
        ("1. Navigate to Project Directory:", "cd 'C:\\Users\\ASUS\\Documents\\Real Time Chat Application'"),
        ("2. Activate Virtual Environment:", ".\\venv\\Scripts\\Activate.ps1   (or run directly via .\\venv\\Scripts\\python.exe)"),
        ("3. Install Required Dependencies:", "pip install -r requirements.txt"),
        ("4. Apply Database Migrations:", "python manage.py makemigrations\npython manage.py migrate"),
        ("5. Seed Demonstration Data:", "python manage.py seed_data"),
        ("6. Run Automated Test Suite:", "python manage.py test"),
        ("7. Launch Real-Time Server:", ".\\run_server.bat   (or python manage.py runserver)")
    ]
    for label, cmd in cmd_steps:
        cp = doc.add_paragraph()
        r = cp.add_run(label + "\n")
        r.bold = True
        rc = cp.add_run(cmd)
        rc.font.name = 'Consolas'
        rc.font.size = Pt(9.5)
        rc.font.color.rgb = RGBColor(30, 41, 59)

    p_browser = doc.add_paragraph()
    p_browser.add_run("Once started, access the application in your browser at: http://127.0.0.1:8000/").bold = True

    # ==================== SECTION 11 ====================
    add_h1("11. PRE-SEEDED DEMONSTRATION ACCOUNTS & VIVA GUIDE")
    add_h2("11.1 Demo User Credentials")
    user_table = doc.add_table(rows=0, cols=4)
    user_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    user_table.columns[0].width = Inches(1.5)
    user_table.columns[1].width = Inches(1.4)
    user_table.columns[2].width = Inches(1.3)
    user_table.columns[3].width = Inches(2.3)
    add_table_row(user_table, ["Username", "Password", "Role", "Description"], is_header=True)
    users_data = [
        ("admin", "admin123", "Superuser", "Full Django Admin access at /admin/"),
        ("rahul_sharma", "password123", "Student Admin", "MCA 4th Sem | Group Admin"),
        ("priya_patel", "password123", "Student Member", "Full Stack Developer"),
        ("amit_verma", "password123", "Student Member", "Backend Architect"),
        ("sneha_reddy", "password123", "Student Member", "UI/UX Designer")
    ]
    for i, row in enumerate(users_data):
        bg = "F8FAFC" if i % 2 == 1 else "FFFFFF"
        add_table_row(user_table, [row[0], row[1], row[2], row[3]], bg_color=bg)

    add_h2("11.2 Recommended Viva Demonstration Steps")
    demo_steps = [
        "1. Open Two Browsers: Open Chrome (normal) and Edge (or Incognito). Log in as rahul_sharma in Window 1 and priya_patel in Window 2.",
        "2. Demonstrate 1-on-1 Chat: Open chat between Rahul and Priya. Start typing in Window 1 and point out the live typing indicator in Window 2. Send a message to demonstrate zero-latency arrival without page refresh.",
        "3. Demonstrate Read Receipts: Observe the checkmark turn to double blue (✓✓) once the message is seen.",
        "4. Demonstrate Group Chat & Options: Open the 'MCA Project Team 2026' group. Click the ⋮ options button to show View Members, Add Member, Leave Group, and Delete Group.",
        "5. Demonstrate Offline Email Notifications: Log out of Priya's account so she is offline. Send a message from Rahul to Priya. Observe the Django terminal print the complete automated email alert with subject, timestamp, and message preview!",
        "6. Demonstrate SQLite Verification: Open DB Browser for SQLite, load db.sqlite3, and show the evaluators the records in auth_user, chat_message, and accounts_userprofile."
    ]
    for d in demo_steps:
        dp = doc.add_paragraph()
        dp.paragraph_format.left_indent = Inches(0.2)
        dp.paragraph_format.space_after = Pt(4)
        dp.add_run(d)

    # ==================== SECTION 12 ====================
    add_h1("12. CONCLUSION & FUTURE ENHANCEMENTS")
    add_h2("12.1 Conclusion")
    p = doc.add_paragraph(
        "The Real-Time Chat Application fulfills all academic and technical requirements for an MCA final project. "
        "By integrating Django Channels with WebSockets, Daphne, and SQLite, the system demonstrates how full-duplex, asynchronous "
        "messaging can be engineered strictly within Python and Django, delivering professional performance and design."
    )

    add_h2("12.2 Potential Future Enhancements")
    fe_items = [
        ("End-to-End Encryption (E2EE): ", "Incorporate client-side Web Crypto API keys for encrypted message payloads."),
        ("WebRTC Audio/Video Calls: ", "Extend WebSocket signaling to support peer-to-peer audio and video streaming."),
        ("Full-Text Message Search: ", "Leverage SQLite FTS5 extension for ultra-fast conversation history searching."),
        ("Web Push Notifications: ", "Integrate browser Service Workers for desktop notifications when tabs are inactive.")
    ]
    for f_title, f_desc in fe_items:
        fep = doc.add_paragraph(style='List Bullet')
        r = fep.add_run(f_title)
        r.bold = True
        fep.add_run(f_desc)

    # Save file
    output_path = os.path.join(os.getcwd(), "Real_Time_Chat_Application_MCA_Project_Report.docx")
    doc.save(output_path)
    print(f"Document successfully created at: {output_path}")


if __name__ == '__main__':
    create_report()

