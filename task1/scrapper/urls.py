from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path("init-session/", views.select_state, name="select_state"),
    path("select-dist/", views.select_dist, name="select_dist"),
    path("court_complex/", views.court_complex, name="court_complex"),
    path("case_details/", views.case_details, name="case_details"),
    path("enter_captcha/", views.enter_captcha, name="enter_captcha"),
    path("results/", views.results, name="results"),
]