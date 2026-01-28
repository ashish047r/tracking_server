from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import Mapping, ScriptAuth
from .services import run_mapping



@csrf_exempt
def get_suffix(request):
    if request.method != "GET":
        return JsonResponse({"success": False}, status=405)

    api_key = request.GET.get("api_key")
    api_secret = request.GET.get("api_secret")

    auth = ScriptAuth.objects.filter(
        api_key=api_key,
        api_secret=api_secret,
        is_active=True
    ).first()

    if not auth:
        return JsonResponse(
            {"success": False, "error": "unauthorized"},
            status=401
        )

    config_name = request.GET.get("config")
    mapping = Mapping.objects.filter(config_name=config_name).first()

    if not mapping:
        return JsonResponse(
            {"success": False, "error": "invalid_config"},
            status=404
        )

    final_suffix = run_mapping(mapping)

    return JsonResponse({
        "success": True,
        "final_suffix": final_suffix
    })
