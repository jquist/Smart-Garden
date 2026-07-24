import secrets
import string

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError


def make_password(length=24):
    alphabet = string.ascii_letters + string.digits + "!#$%*?-_"
    return "".join(secrets.choice(alphabet) for _ in range(length))


class Command(BaseCommand):
    help = "Create or update a staff/superuser account for development work."

    def add_arguments(self, parser):
        parser.add_argument("--username", default="dev_jquist")
        parser.add_argument("--email", default="jquist1234566@gmail.com")
        parser.add_argument("--password", default="")
        parser.add_argument(
            "--staff-only",
            action="store_true",
            help="Make the account staff without full superuser access.",
        )

    def handle(self, *args, **options):
        username = str(options["username"]).strip()
        email = str(options["email"]).strip()
        password = str(options["password"] or "").strip() or make_password()

        if not username or not email:
            raise CommandError("Both --username and --email are required.")

        User = get_user_model()
        username_match = User.objects.filter(username__iexact=username).first()
        email_match = User.objects.filter(email__iexact=email).first()

        if username_match and email_match and username_match.pk != email_match.pk:
            raise CommandError("Username and email belong to different accounts.")

        user = username_match or email_match or User(username=username)
        created = user.pk is None
        user.username = username
        user.email = email
        user.is_staff = True
        user.is_superuser = not options["staff_only"]
        user.is_active = True

        try:
            validate_password(password, user)
        except ValidationError as error:
            raise CommandError(" ".join(error.messages))

        user.set_password(password)
        user.save()

        action = "Created" if created else "Updated"
        role = "staff" if options["staff_only"] else "staff + superuser"

        self.stdout.write(self.style.SUCCESS(f"{action} {role} account: {username}"))
        self.stdout.write(f"Email: {email}")
        self.stdout.write(f"Password: {password}")
