from django.contrib import admin
from .models import Mapping, RunLog, ScriptAuth
from .services import run_mapping


@admin.register(ScriptAuth)
class ScriptAuthAdmin(admin.ModelAdmin):
    list_display = ("name", "api_key", "is_active", "created_at")
    list_filter = ("is_active",)


@admin.register(Mapping)
class MappingAdmin(admin.ModelAdmin):
    list_display = (
        "config_name",
        "extract_all_params",
        "updated_at",
    )

    readonly_fields = ("last_suffix", "last_run_at", "updated_at")

    fields = (
        "config_name",
        "tracking_url",
        "extract_all_params",
        "params",
        "last_suffix",
        "last_run_at",
        "updated_at",
    )

    actions = ["run_selected_mappings"]

    def run_selected_mappings(self, request, queryset):
        for mapping in queryset:
            try:
                run_mapping(mapping)
                self.message_user(
                    request,
                    f"Successfully ran {mapping.config_name}"
                )
            except Exception as e:
                self.message_user(
                    request,
                    f"Error running {mapping.config_name}: {e}",
                    level="error"
                )

    run_selected_mappings.short_description = "Run selected mappings now"


@admin.register(RunLog)
class RunLogAdmin(admin.ModelAdmin):
    list_display = ("mapping", "time", "success")
    readonly_fields = ("final_url", "extracted_value", "error_message", "time")
    list_filter = ("success",)
