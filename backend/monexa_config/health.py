"""Health / readiness — anonymes, sans secrets."""
from django.db import connection
from django.http import JsonResponse
from django.views.decorators.http import require_GET


@require_GET
def health(_request):
    return JsonResponse({"status": "ok", "service": "monexa"})


@require_GET
def ready(_request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return JsonResponse({"status": "ready", "database": "ok"})
    except Exception:
        return JsonResponse({"status": "not_ready", "database": "error"}, status=503)
