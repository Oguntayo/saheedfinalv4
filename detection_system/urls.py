from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name="home"),
    path('about', views.about, name="about"),
    path('register/', views.registerPage, name="register"),
    path('login/', views.loginPage, name="login"),
    path('logout/', views.logoutUser, name="logout"),
    path('profile/<str:pk>/', views.profile, name="profile"),
    path('dashboard/', views.dashboard, name="dashboard"),
    path('analytics/', views.analytics, name="analytics"),
    path('support/', views.support, name="support"),
    path('upload/', views.upload, name="upload"),
    path('camera/', views.camera, name="camera"),
    path('predict/', views.predict, name="predict"),
    ]