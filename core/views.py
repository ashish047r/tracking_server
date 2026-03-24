from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import Mapping, ScriptAuth
from .services import run_mapping, run_mapping_batch


def _authenticate(request):
    api_key = request.GET.get("api_key")
    api_secret = request.GET.get("api_secret")
    return ScriptAuth.objects.filter(
        api_key=api_key, api_secret=api_secret, is_active=True
    ).first()


def _get_mapping(request):
    config_name = request.GET.get("config")
    return Mapping.objects.filter(config_name=config_name).first()


@csrf_exempt
def get_suffix(request):
    if request.method != "GET":
        return JsonResponse({"success": False}, status=405)

    if not _authenticate(request):
        return JsonResponse({"success": False, "error": "unauthorized"}, status=401)

    mapping = _get_mapping(request)
    if not mapping:
        return JsonResponse({"success": False, "error": "invalid_config"}, status=404)

    final_suffix = run_mapping(mapping)

    return JsonResponse({"success": True, "final_suffix": final_suffix})


@csrf_exempt
def get_batch_suffix(request):
    if request.method != "GET":
        return JsonResponse({"success": False}, status=405)

    if not _authenticate(request):
        return JsonResponse({"success": False, "error": "unauthorized"}, status=401)

    mapping = _get_mapping(request)
    if not mapping:
        return JsonResponse({"success": False, "error": "invalid_config"}, status=404)

    count = min(int(request.GET.get("count", 10)), 50)

    suffixes, errors = run_mapping_batch(mapping, count)

    return JsonResponse({
        "success": True,
        "suffixes": suffixes,
        "count": len(suffixes),
        "errors": len(errors),
        "error_details": errors[:5],
    })
