from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from django.utils import timezone

from banking.models import RegistrationStatus, UserProfile, UserRole
from banking.services import create_account_for_user, deposit


class Command(BaseCommand):
    help = 'Create demo FinTrack users for local frontend/backend testing.'

    def handle(self, *args, **options):
        User = get_user_model()
        admin, _ = User.objects.get_or_create(
            username='admin',
            defaults={'email': 'admin@fintrack.local', 'is_staff': True, 'is_superuser': True},
        )
        admin.is_staff = True
        admin.is_superuser = True
        admin.set_password('admin123')
        admin.save()
        UserProfile.objects.update_or_create(
            user=admin,
            defaults={
                'role': UserRole.ADMIN,
                'status': RegistrationStatus.ACTIVE,
                'approved_by': admin,
                'approved_at': timezone.now(),
                'rejection_reason': '',
            },
        )

        employee, _ = User.objects.get_or_create(username='employee', defaults={'email': 'employee@fintrack.local'})
        employee.set_password('employee123')
        employee.save()
        UserProfile.objects.update_or_create(
            user=employee,
            defaults={
                'role': UserRole.EMPLOYEE,
                'status': RegistrationStatus.ACTIVE,
                'approved_by': admin,
                'approved_at': timezone.now(),
                'rejection_reason': '',
            },
        )

        member, _ = User.objects.get_or_create(username='member', defaults={'email': 'member@fintrack.local'})
        member.set_password('member123')
        member.save()
        UserProfile.objects.update_or_create(
            user=member,
            defaults={
                'role': UserRole.CUSTOMER,
                'status': RegistrationStatus.ACTIVE,
                'approved_by': admin,
                'approved_at': timezone.now(),
                'rejection_reason': '',
            },
        )

        alice, _ = User.objects.get_or_create(username='alice', defaults={'email': 'alice@fintrack.local'})
        alice.set_password('alice123')
        alice.save()
        UserProfile.objects.update_or_create(
            user=alice,
            defaults={
                'role': UserRole.CUSTOMER,
                'status': RegistrationStatus.ACTIVE,
                'approved_by': admin,
                'approved_at': timezone.now(),
                'rejection_reason': '',
            },
        )

        bob, _ = User.objects.get_or_create(username='bob', defaults={'email': 'bob@fintrack.local'})
        bob.set_password('bob123')
        bob.save()
        UserProfile.objects.update_or_create(
            user=bob,
            defaults={
                'role': UserRole.CUSTOMER,
                'status': RegistrationStatus.ACTIVE,
                'approved_by': admin,
                'approved_at': timezone.now(),
                'rejection_reason': '',
            },
        )

        create_account_for_user(admin)
        create_account_for_user(employee)
        create_account_for_user(member)
        create_account_for_user(alice)
        create_account_for_user(bob)

        if member.bank_account.balance == 0:
            deposit(member, Decimal('1500.00'), 'Demo member opening balance')
        if alice.bank_account.balance == 0:
            deposit(alice, Decimal('2500.00'), 'Demo opening balance')
        if bob.bank_account.balance == 0:
            deposit(bob, Decimal('750.00'), 'Demo opening balance')

        self.stdout.write(self.style.SUCCESS('Demo users ready: admin/admin123, employee/employee123, member/member123, alice/alice123, bob/bob123'))
