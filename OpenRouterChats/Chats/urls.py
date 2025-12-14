from django.urls import path

from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('send/', views.send_message, name='send_message'),
    path('models/', views.get_all_models, name='get_all_models'),
]
