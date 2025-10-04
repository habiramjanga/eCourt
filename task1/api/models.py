from django.db import models
from django.contrib.auth.models import User

class UserQueryLog(models.Model):
    # If you have user authentication
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    # Session information
    session_key = models.CharField(max_length=40, null=True, blank=True)

    # Request information
    endpoint = models.CharField(max_length=100)
    request_data = models.JSONField()
    request_timestamp = models.DateTimeField(auto_now_add=True)

    # Response information
    response_data = models.JSONField()
    response_timestamp = models.DateTimeField(auto_now=True)
    status_code = models.IntegerField()

    # Additional metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.endpoint} - {self.request_timestamp}"

    class Meta:
        ordering = ['-request_timestamp']
        verbose_name = "User Query Log"
        verbose_name_plural = "User Query Logs"
