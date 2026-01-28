from django.db import models


class ScriptAuth(models.Model):
    name = models.CharField(max_length=100)
    api_key = models.CharField(max_length=64, unique=True)
    api_secret = models.CharField(max_length=128)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Mapping(models.Model):
    """
    One mapping == one Google Ads campaign name
    """
    config_name = models.CharField(
        max_length=200,
        unique=True,
        help_text="Must exactly match Google Ads campaign name"
    )

    tracking_url = models.URLField()

    params = models.JSONField(default=list, blank=True)

    extract_all_params = models.BooleanField(
        default=False,
        help_text="If enabled, extract ALL query params from final redirect URL"
    )

    last_run_at = models.DateTimeField(blank=True, null=True)
    last_suffix = models.TextField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        self.config_name = self.config_name.strip()

    def __str__(self):
        return self.config_name


class RunLog(models.Model):
    mapping = models.ForeignKey(Mapping, on_delete=models.CASCADE)
    time = models.DateTimeField(auto_now_add=True)
    final_url = models.TextField(blank=True, null=True)
    extracted_value = models.TextField(blank=True, null=True)
    success = models.BooleanField(default=False)
    error_message = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.mapping.config_name} @ {self.time}"
