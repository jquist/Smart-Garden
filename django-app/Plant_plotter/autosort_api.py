from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .autosort_service import run_autosort


@api_view(["POST"])
def autosort_view(request):
    try:
        result = run_autosort(request.data)
        return Response(result, status=status.HTTP_200_OK)
    except ValueError as exc:
        return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as exc:
        return Response(
            {"error": "Autosort failed", "details": str(exc)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
