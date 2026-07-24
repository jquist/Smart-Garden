import json

from .models import Plant, GardenPlan, Companion_helpslistItem, Companion_helped_bylistItem, Plants_avoidlistItem
from django.contrib.auth import authenticate, get_user_model, login, logout, update_session_auth_hash
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_email
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods, require_POST
from django.db.models import Count, Q
from django.http import JsonResponse
from rest_framework import permissions, viewsets

from .serializers import PlantSerializer, GardenPlanSerializer, Companion_helpslistItemSerializer, Companion_helped_bylistItemSerializer, Plants_avoidlistItemSerializer


def user_payload(user):
    if not user.is_authenticated:
        return {"is_authenticated": False, "user": None}

    return {
        "is_authenticated": True,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_staff": user.is_staff,
            "is_superuser": user.is_superuser,
        },
    }


def read_json_body(request):
    try:
        return json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return None


def validate_optional_email(email):
    if not email:
        return ""

    try:
        validate_email(email)
    except DjangoValidationError:
        return None

    return email


@ensure_csrf_cookie
@require_http_methods(["GET"])
def auth_me_view(request):
    return JsonResponse(user_payload(request.user))


@ensure_csrf_cookie
@require_http_methods(["GET"])
def csrf_view(request):
    return JsonResponse({"ok": True})


@require_POST
def signup_view(request):
    data = read_json_body(request)
    if data is None:
        return JsonResponse({"error": "Invalid request."}, status=400)

    username = str(data.get("username", "")).strip()
    email = str(data.get("email", "")).strip()
    password = str(data.get("password", ""))

    if not username or not password:
        return JsonResponse({"error": "Username and password are required."}, status=400)
    if len(username) > 150:
        return JsonResponse({"error": "Username must be 150 characters or fewer."}, status=400)

    email = validate_optional_email(email)
    if email is None:
        return JsonResponse({"error": "Enter a valid email address."}, status=400)

    User = get_user_model()
    if User.objects.filter(username__iexact=username).exists():
        return JsonResponse({"error": "That username is already taken."}, status=400)
    if email and User.objects.filter(email__iexact=email).exists():
        return JsonResponse({"error": "That email is already linked to an account."}, status=400)

    try:
        validate_password(password, User(username=username, email=email))
    except DjangoValidationError as error:
        return JsonResponse({"error": " ".join(error.messages)}, status=400)

    user = User.objects.create_user(username=username, email=email, password=password)
    login(request, user)
    return JsonResponse(user_payload(user), status=201)


@require_POST
def login_view(request):
    data = read_json_body(request)
    if data is None:
        return JsonResponse({"error": "Invalid request."}, status=400)

    username = str(data.get("username", "")).strip()
    password = str(data.get("password", ""))
    user = authenticate(request, username=username, password=password)

    if user is None:
        return JsonResponse({"error": "Username or password was not recognised."}, status=400)

    login(request, user)
    return JsonResponse(user_payload(user))


@require_POST
def logout_view(request):
    logout(request)
    return JsonResponse(user_payload(request.user))


@require_http_methods(["GET", "PUT"])
def profile_view(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Log in to manage your profile."}, status=401)

    if request.method == "GET":
        return JsonResponse(user_payload(request.user))

    data = read_json_body(request)
    if data is None:
        return JsonResponse({"error": "Invalid request."}, status=400)

    username = str(data.get("username", "")).strip()
    email = str(data.get("email", "")).strip()

    if not username:
        return JsonResponse({"error": "Username is required."}, status=400)
    if len(username) > 150:
        return JsonResponse({"error": "Username must be 150 characters or fewer."}, status=400)

    email = validate_optional_email(email)
    if email is None:
        return JsonResponse({"error": "Enter a valid email address."}, status=400)

    User = get_user_model()
    username_exists = (
        User.objects.filter(username__iexact=username)
        .exclude(id=request.user.id)
        .exists()
    )
    if username_exists:
        return JsonResponse({"error": "That username is already taken."}, status=400)

    email_exists = (
        email
        and User.objects.filter(email__iexact=email)
        .exclude(id=request.user.id)
        .exists()
    )
    if email_exists:
        return JsonResponse({"error": "That email is already linked to an account."}, status=400)

    request.user.username = username
    request.user.email = email
    request.user.save(update_fields=["username", "email"])
    return JsonResponse(user_payload(request.user))


@require_POST
def password_view(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Log in to change your password."}, status=401)

    data = read_json_body(request)
    if data is None:
        return JsonResponse({"error": "Invalid request."}, status=400)

    current_password = str(data.get("current_password") or data.get("old_password") or "")
    new_password = str(data.get("new_password", ""))

    if not current_password or not new_password:
        return JsonResponse({"error": "Current password and new password are required."}, status=400)
    if not request.user.check_password(current_password):
        return JsonResponse({"error": "Current password was not recognised."}, status=400)

    try:
        validate_password(new_password, request.user)
    except DjangoValidationError as error:
        return JsonResponse({"error": " ".join(error.messages)}, status=400)

    request.user.set_password(new_password)
    request.user.save(update_fields=["password"])
    update_session_auth_hash(request, request.user)
    return JsonResponse({"ok": True})

class PlantViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = Plant.objects.prefetch_related(
        "companion_helps",
        "companion_helped_by",
        "plants_avoid",
    ).all()
    serializer_class = PlantSerializer

    def get_queryset(self):
        qs = super().get_queryset().order_by("plant_category", "name")
        category = self.request.query_params.get("category")
        search = self.request.query_params.get("search")

        if category:
            qs = qs.filter(plant_category=category)
        if search:
            qs = qs.filter(
                Q(name__icontains=search)
                | Q(plant_category__icontains=search)
                | Q(description__icontains=search)
                | Q(planting_tips__icontains=search)
                | Q(planting_how_to__icontains=search)
            )

        return qs


class GardenPlanViewSet(viewsets.ModelViewSet):
    serializer_class = GardenPlanSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = GardenPlan.objects.filter(owner=self.request.user)
        plan_type = self.request.query_params.get("plan_type")
        if plan_type:
            qs = qs.filter(plan_type=plan_type)
        return qs

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def perform_update(self, serializer):
        serializer.save(owner=self.request.user)


class Companion_helpslistItemViewSet(viewsets.ModelViewSet):
    queryset = Companion_helpslistItem.objects.all()
    serializer_class = Companion_helpslistItemSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        plant_id = self.request.query_params.get("plant")
        if plant_id:
            qs = qs.filter(plant_id=plant_id)
        return qs


class Companion_helped_bylistItemViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = Companion_helped_bylistItem.objects.all()
    serializer_class = Companion_helped_bylistItemSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        plant_id = self.request.query_params.get("plant")
        if plant_id:
            qs = qs.filter(plant_id=plant_id)
        return qs

class Plants_avoidlistItemViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = Plants_avoidlistItem.objects.all()
    serializer_class = Plants_avoidlistItemSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        plant_id = self.request.query_params.get("plant")
        if plant_id:
            qs = qs.filter(plant_id=plant_id)
        return qs


def plant_summary_view(request):
    categories = {
        row["plant_category"]: row["count"]
        for row in Plant.objects.values("plant_category")
        .annotate(count=Count("id"))
        .order_by("plant_category")
    }
    weed_examples = list(
        Plant.objects.filter(plant_category="weed")
        .order_by("name")
        .values_list("name", flat=True)[:50]
    )

    return JsonResponse(
        {
            "total": Plant.objects.count(),
            "categories": categories,
            "weed_count": categories.get("weed", 0),
            "groundsel_exists": Plant.objects.filter(name="Groundsel").exists(),
            "weed_examples": weed_examples,
        }
    )

