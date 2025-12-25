from django.urls import path

from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    # send new message to LLM
    path('send/', views.send_message, name='send_message'),
    # get all(update list) openRouter models
    path('models/', views.get_all_models, name='get_all_models'),
    # get all teachers
    path('teachers/', views.get_all_teachers, name='get_all_teachers'),
    # create a new teacher
    path('teachers/create/', views.create_new_teacher, name='create_new_teacher'),
    # get real-time Django messages
    path('messages/', views.get_messages_view, name='get_messages'),
]
