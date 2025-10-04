from django.urls import path
from . import views

urlpatterns = [
    path('',views.driver_loader,name='driver_loader'),
    # user auth paths
    path('register/', views.register_user, name='register_user'),
    path('login/', views.login_user, name='login_user'),
    path('users/', views.users, name='users'),
    path('logout/', views.logout_user, name='logout_user'),

    # application logic paths
    path('set_district_and_get_courts/',views.set_district_and_get_courts,name='set_district_and_get_courts'),
    path('set_court_and_get_case_types/',views.set_court_and_get_case_types,name='set_court_and_get_case_types'),
    path('post_case_inputs/',views.post_case_inputs,name='post_case_inputs'),
    path('close_driver/',views.close_driver,name='close_driver'),
    path('download_pdf/',views.download_latest_order,name='download_pdf'),
    path('logs/', views.get_user_query_logs, name='get_user_query_logs'),
]