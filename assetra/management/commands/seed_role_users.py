from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from assetra.models import Tenant, TenantMembership


class Command(BaseCommand):
    help = "Create or update standard role users for a tenant (read_only and operator)."

    def add_arguments(self, parser):
        parser.add_argument("--tenant-id", type=int, default=1, help="Tenant ID to assign memberships to (default: 1)")
        parser.add_argument(
            "--password",
            type=str,
            default="StdUserPass123!",
            help="Password applied to seeded users (default: StdUserPass123!)",
        )

    def handle(self, *args, **options):
        tenant_id = options["tenant_id"]
        password = options["password"]

        try:
            tenant = Tenant.objects.get(id=tenant_id)
        except Tenant.DoesNotExist as exc:
            raise CommandError(f"Tenant {tenant_id} does not exist") from exc

        user_model = get_user_model()
        users_to_seed = [
            ("std_readonly", TenantMembership.Role.READ_ONLY),
            ("std_operator", TenantMembership.Role.OPERATOR),
        ]

        for username, role in users_to_seed:
            user, _created = user_model.objects.get_or_create(
                username=username,
                defaults={
                    "is_active": True,
                },
            )
            user.is_active = True
            user.set_password(password)
            user.save(update_fields=["is_active", "password"])

            membership, _membership_created = TenantMembership.objects.update_or_create(
                tenant=tenant,
                user=user,
                defaults={"role": role},
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f"{username} configured: tenant={tenant.id} role={membership.role}",
                ),
            )

        self.stdout.write(self.style.SUCCESS("Role user seeding complete."))
