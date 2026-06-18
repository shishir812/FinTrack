from decimal import Decimal

from django.contrib.auth import get_user_model
from django.utils import timezone
from django.test import TestCase, override_settings

from .jwt_utils import create_token
from .models import Beneficiary, InstallmentStatus, LoanStatus, Notification, RegistrationStatus, TransactionStatus, UserProfile, UserRole
from .services import (
    approve_loan, approve_transaction, create_account_for_user, deposit, issue_loan,
    pay_loan_installment, sync_overdue_installments, transfer, withdraw,
)


@override_settings(FINTRACK_LARGE_TRANSACTION_LIMIT=Decimal('1000.00'))
class TransactionFlowTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username='alice', password='secret123')
        self.receiver = User.objects.create_user(username='bob', password='secret123')
        self.admin = User.objects.create_user(username='admin', password='secret123', is_staff=True)
        self.employee = User.objects.create_user(username='employee', password='secret123')
        UserProfile.objects.update_or_create(user=self.employee, defaults={'role': UserRole.EMPLOYEE})
        self.account = create_account_for_user(self.user)
        self.receiver_account = create_account_for_user(self.receiver)

    def test_failed_withdrawal_does_not_change_balance(self):
        txn = withdraw(self.user, Decimal('50.00'), 'Too much')
        self.account.refresh_from_db()
        self.assertEqual(txn.status, TransactionStatus.FAILED)
        self.assertEqual(self.account.balance, Decimal('0.00'))

    def test_transfer_deducts_sender_and_adds_receiver(self):
        deposit(self.user, Decimal('200.00'), 'Seed')
        txn = transfer(self.user, self.receiver_account.account_number, Decimal('75.00'), 'Pay Bob')
        self.account.refresh_from_db()
        self.receiver_account.refresh_from_db()
        self.assertEqual(txn.status, TransactionStatus.SUCCESS)
        self.assertEqual(self.account.balance, Decimal('125.00'))
        self.assertEqual(self.receiver_account.balance, Decimal('75.00'))

    def test_transfer_accepts_receiver_username(self):
        deposit(self.user, Decimal('200.00'), 'Seed')
        txn = transfer(self.user, self.receiver.username, Decimal('50.00'), 'Pay by username')
        self.account.refresh_from_db()
        self.receiver_account.refresh_from_db()
        self.assertEqual(txn.status, TransactionStatus.SUCCESS)
        self.assertEqual(self.account.balance, Decimal('150.00'))
        self.assertEqual(self.receiver_account.balance, Decimal('50.00'))

    def test_can_add_beneficiary_by_username(self):
        self.client.defaults['HTTP_AUTHORIZATION'] = f'Bearer {create_token(self.user)}'
        response = self.client.post('/api/beneficiaries/', {'account_number': self.receiver.username, 'nickname': 'Bob'})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['username'], self.receiver.username)

    def test_transfer_accepts_saved_beneficiary_id(self):
        deposit(self.user, Decimal('200.00'), 'Seed')
        beneficiary = Beneficiary.objects.create(owner=self.user, account=self.receiver_account, nickname='Bob')
        self.client.defaults['HTTP_AUTHORIZATION'] = f'Bearer {create_token(self.user)}'
        response = self.client.post('/api/transactions/transfer/', {
            'beneficiary_id': beneficiary.id,
            'amount': '60.00',
            'description': 'Beneficiary transfer',
        })
        self.account.refresh_from_db()
        self.receiver_account.refresh_from_db()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['status'], TransactionStatus.SUCCESS)
        self.assertEqual(self.account.balance, Decimal('140.00'))
        self.assertEqual(self.receiver_account.balance, Decimal('60.00'))

    def test_login_requires_matching_role_portal(self):
        response = self.client.post('/api/auth/login/', {
            'username': self.employee.username,
            'password': 'secret123',
            'role': UserRole.EMPLOYEE,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['user']['role'], UserRole.EMPLOYEE)

        mismatch = self.client.post('/api/auth/login/', {
            'username': self.employee.username,
            'password': 'secret123',
            'role': UserRole.CUSTOMER,
        })
        self.assertEqual(mismatch.status_code, 400)

    def test_admin_can_register_employee_directly(self):
        self.client.defaults['HTTP_AUTHORIZATION'] = f'Bearer {create_token(self.admin)}'
        response = self.client.post('/api/auth/register/', {
            'username': 'newemployee',
            'email': 'newemployee@fintrack.local',
            'password': 'secret123',
            'role': UserRole.EMPLOYEE,
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['profile']['status'], RegistrationStatus.ACTIVE)
        self.assertEqual(response.data['user']['role'], UserRole.EMPLOYEE)
        self.assertTrue(get_user_model().objects.get(username='newemployee').bank_account)

    def test_admin_can_update_employee_or_member_profile(self):
        self.client.defaults['HTTP_AUTHORIZATION'] = f'Bearer {create_token(self.admin)}'
        employee_account = create_account_for_user(self.employee)
        response = self.client.patch(
            f'/api/admin/accounts/{employee_account.id}/profile/',
            {
                'first_name': 'Branch',
                'last_name': 'Officer',
                'email': 'officer@fintrack.local',
                'location': 'Dhaka',
                'phone_number': '+8801712345678',
                'password': 'updated123',
            },
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        self.employee.refresh_from_db()
        self.employee.profile.refresh_from_db()
        self.assertEqual(self.employee.first_name, 'Branch')
        self.assertEqual(self.employee.last_name, 'Officer')
        self.assertEqual(self.employee.email, 'officer@fintrack.local')
        self.assertEqual(self.employee.profile.location, 'Dhaka')
        self.assertEqual(self.employee.profile.phone_number, '+8801712345678')
        self.assertTrue(self.employee.check_password('updated123'))

    def test_admin_profile_cannot_be_updated_from_account_editor(self):
        self.client.defaults['HTTP_AUTHORIZATION'] = f'Bearer {create_token(self.admin)}'
        admin_account = create_account_for_user(self.admin)
        response = self.client.patch(
            f'/api/admin/accounts/{admin_account.id}/profile/',
            {'first_name': 'Changed'},
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)

    def test_employee_member_registration_requires_admin_approval(self):
        self.client.defaults['HTTP_AUTHORIZATION'] = f'Bearer {create_token(self.employee)}'
        response = self.client.post('/api/auth/register/', {
            'username': 'pendingmember',
            'email': 'pendingmember@fintrack.local',
            'password': 'secret123',
            'role': UserRole.CUSTOMER,
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['profile']['status'], RegistrationStatus.PENDING)

        pending_user = get_user_model().objects.get(username='pendingmember')
        login_before_approval = self.client.post('/api/auth/login/', {
            'username': 'pendingmember',
            'password': 'secret123',
            'role': UserRole.CUSTOMER,
        })
        self.assertEqual(login_before_approval.status_code, 400)

        self.client.defaults['HTTP_AUTHORIZATION'] = f'Bearer {create_token(self.admin)}'
        profile = pending_user.profile
        approval = self.client.post(f'/api/admin/registrations/{profile.id}/approve/')
        self.assertEqual(approval.status_code, 200)
        profile.refresh_from_db()
        self.assertEqual(profile.status, RegistrationStatus.ACTIVE)
        self.assertTrue(hasattr(pending_user, 'bank_account'))

    def test_employee_deposit_waits_for_admin_approval_then_goes_to_admin_account(self):
        admin_account = create_account_for_user(self.admin)
        employee_account = create_account_for_user(self.employee)
        txn = deposit(self.employee, Decimal('300.00'), 'Counter cash deposit')
        admin_account.refresh_from_db()
        employee_account.refresh_from_db()
        self.assertEqual(txn.status, TransactionStatus.PENDING)
        self.assertTrue(txn.requires_approval)
        self.assertEqual(txn.receiver_id, admin_account.id)
        self.assertEqual(admin_account.balance, Decimal('0.00'))
        self.assertEqual(employee_account.balance, Decimal('0.00'))
        self.assertTrue(Notification.objects.filter(user=self.admin, title='Employee deposit pending approval').exists())

        approve_transaction(self.admin, txn.id)
        admin_account.refresh_from_db()
        employee_account.refresh_from_db()
        txn.refresh_from_db()
        self.assertEqual(txn.status, TransactionStatus.SUCCESS)
        self.assertEqual(admin_account.balance, Decimal('300.00'))
        self.assertEqual(employee_account.balance, Decimal('0.00'))

    def test_all_admins_share_employee_deposit_settlement_account(self):
        User = get_user_model()
        second_admin = User.objects.create_user(username='branchadmin', password='secret123', is_staff=True)
        shared_admin_account = create_account_for_user(self.admin)
        second_admin_visible_account = create_account_for_user(second_admin)
        txn = deposit(self.employee, Decimal('450.00'), 'Branch cash deposit')

        approve_transaction(second_admin, txn.id)

        txn.refresh_from_db()
        shared_admin_account.refresh_from_db()
        second_admin_visible_account.refresh_from_db()
        self.assertEqual(shared_admin_account.id, second_admin_visible_account.id)
        self.assertEqual(txn.status, TransactionStatus.SUCCESS)
        self.assertEqual(txn.receiver_id, shared_admin_account.id)
        self.assertEqual(shared_admin_account.balance, Decimal('450.00'))
        self.assertEqual(second_admin_visible_account.balance, Decimal('450.00'))

    def test_employee_can_issue_loan_and_customer_can_pay_installment(self):
        loan = issue_loan(self.employee, self.user, Decimal('1200.00'), Decimal('12.00'), 12, 'Test loan')
        self.account.refresh_from_db()
        self.assertEqual(loan.status, LoanStatus.PENDING)
        self.assertEqual(self.account.balance, Decimal('0.00'))
        loan = approve_loan(self.admin, loan.id)
        self.account.refresh_from_db()
        self.assertEqual(loan.status, LoanStatus.ACTIVE)
        self.assertEqual(self.account.balance, Decimal('1200.00'))
        self.assertEqual(loan.installments.count(), 12)
        first_installment = loan.installments.first()
        paid = pay_loan_installment(self.user, first_installment.id)
        self.account.refresh_from_db()
        self.assertEqual(paid.status, InstallmentStatus.PAID)
        self.assertEqual(self.account.balance, Decimal('1088.00'))

    def test_overdue_installment_notifies_customer(self):
        loan = issue_loan(self.employee, self.user, Decimal('600.00'), Decimal('12.00'), 6, 'Overdue loan')
        loan = approve_loan(self.admin, loan.id)
        installment = loan.installments.first()
        installment.due_date = timezone.localdate() - timezone.timedelta(days=1)
        installment.save(update_fields=['due_date'])
        overdue = sync_overdue_installments()
        installment.refresh_from_db()
        self.assertEqual(len(overdue), 1)
        self.assertEqual(installment.status, InstallmentStatus.OVERDUE)
        self.assertTrue(Notification.objects.filter(user=self.user, title='Loan payment overdue').exists())

    def test_large_withdrawal_is_pending_until_admin_approval(self):
        deposit(self.user, Decimal('1500.00'), 'Large deposit')
        pending_deposit = self.user.created_transactions.get(amount=Decimal('1500.00'))
        approve_transaction(self.admin, pending_deposit.id)
        txn = withdraw(self.user, Decimal('1000.00'), 'Large withdrawal')
        self.account.refresh_from_db()
        self.assertEqual(txn.status, TransactionStatus.PENDING)
        self.assertEqual(self.account.balance, Decimal('1500.00'))
        approve_transaction(self.admin, txn.id)
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal('500.00'))
