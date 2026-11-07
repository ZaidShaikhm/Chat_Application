from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('chat/<str:username>/', views.private_chat_view, name='private_chat'),
    path('group/<int:group_id>/', views.group_chat_view, name='group_chat'),
    path('group/create/', views.create_group_view, name='create_group'),
    path('group/<int:group_id>/add-member/', views.add_group_member_view, name='add_group_member'),
    path('group/<int:group_id>/leave/', views.leave_group_view, name='leave_group'),
    path('group/<int:group_id>/delete/', views.delete_group_view, name='delete_group'),
    path('group/<int:group_id>/join/', views.join_group_view, name='join_group'),
    path('group/<int:group_id>/remove-member/<int:user_id>/', views.remove_group_member_view, name='remove_group_member'),
    path('api/upload/', views.file_upload_view, name='file_upload'),
]
