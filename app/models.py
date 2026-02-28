from django.db import models
from django.contrib.auth import get_user_model


User = get_user_model()


class Website(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='websites')

    website_name = models.CharField(max_length=100)
    website_url = models.URLField(max_length=50)

    interval = models.IntegerField(help_text='minutes')

    last_checked = models.DateTimeField(null=True, blank=True, db_index=True)
    last_status = models.BooleanField(null=True)
    last_response_time = models.FloatField(null=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.website_name} - {self.user.username}"


class CheckResult(models.Model):
    website = models.ForeignKey(Website, on_delete=models.CASCADE, related_name="checks")
    checked_at = models.DateTimeField(auto_now_add=True)
    status = models.BooleanField()  # up / down
    status_code = models.IntegerField(null=True, blank=True)
    response_time = models.FloatField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ["-checked_at"]
        indexes = [
            models.Index(fields=["website", "checked_at"]),
        ]

    def __str__(self):
        return f"{self.website.website_name}"