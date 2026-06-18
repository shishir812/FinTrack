from django.conf import settings
from django.db import models
from django.utils import timezone


class AccountStatus(models.TextChoices):
    ACTIVE = 'ACTIVE', 'Active'
    FROZEN = 'FROZEN', 'Frozen'
    CLOSED = 'CLOSED', 'Closed'


class TransactionType(models.TextChoices):
    DEPOSIT = 'DEPOSIT', 'Deposit'
    WITHDRAWAL = 'WITHDRAWAL', 'Withdrawal'
    TRANSFER = 'TRANSFER', 'Transfer'
    LOAN_ISSUE = 'LOAN_ISSUE', 'Loan Issue'
    LOAN_PAYMENT = 'LOAN_PAYMENT', 'Loan Payment'


class TransactionStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    SUCCESS = 'SUCCESS', 'Success'
    FAILED = 'FAILED', 'Failed'
    REJECTED = 'REJECTED', 'Rejected'


class UserRole(models.TextChoices):
    ADMIN = 'ADMIN', 'Admin'
    EMPLOYEE = 'EMPLOYEE', 'Bank Employee'
    CUSTOMER = 'CUSTOMER', 'Customer'


class RegistrationStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending Approval'
    ACTIVE = 'ACTIVE', 'Active'
    REJECTED = 'REJECTED', 'Rejected'


class LoanStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending Approval'
    ACTIVE = 'ACTIVE', 'Active'
    PAID = 'PAID', 'Paid'
    DEFAULTED = 'DEFAULTED', 'Defaulted'
    REJECTED = 'REJECTED', 'Rejected'


class InstallmentStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    PAID = 'PAID', 'Paid'
    OVERDUE = 'OVERDUE', 'Overdue'


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=12, choices=UserRole.choices, default=UserRole.CUSTOMER)
    status = models.CharField(max_length=12, choices=RegistrationStatus.choices, default=RegistrationStatus.ACTIVE)
    location = models.CharField(max_length=120, blank=True)
    phone_number = models.CharField(max_length=30, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='created_profiles')
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='approved_profiles')
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} - {self.role} - {self.status}'


class BankAccount(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bank_account')
    account_number = models.CharField(max_length=20, unique=True)
    balance = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    status = models.CharField(max_length=12, choices=AccountStatus.choices, default=AccountStatus.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.account_number} - {self.user.username}'


class Beneficiary(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='beneficiaries')
    account = models.ForeignKey(BankAccount, on_delete=models.CASCADE, related_name='listed_by')
    nickname = models.CharField(max_length=80, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('owner', 'account')

    def __str__(self):
        return self.nickname or self.account.account_number


class Transaction(models.Model):
    transaction_type = models.CharField(max_length=12, choices=TransactionType.choices)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    sender = models.ForeignKey(BankAccount, null=True, blank=True, on_delete=models.SET_NULL, related_name='sent_transactions')
    receiver = models.ForeignKey(BankAccount, null=True, blank=True, on_delete=models.SET_NULL, related_name='received_transactions')
    status = models.CharField(max_length=12, choices=TransactionStatus.choices, default=TransactionStatus.PENDING)
    description = models.CharField(max_length=255, blank=True)
    failure_reason = models.CharField(max_length=255, blank=True)
    requires_approval = models.BooleanField(default=False)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='approved_transactions')
    approved_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='created_transactions')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def mark_success(self, admin_user=None):
        self.status = TransactionStatus.SUCCESS
        self.approved_by = admin_user or self.approved_by
        self.approved_at = timezone.now() if admin_user else self.approved_at
        self.failure_reason = ''
        self.save(update_fields=['status', 'approved_by', 'approved_at', 'failure_reason', 'updated_at'])

    def __str__(self):
        return f'{self.transaction_type} {self.amount} {self.status}'


class AuditLog(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=80)
    transaction = models.ForeignKey(Transaction, null=True, blank=True, on_delete=models.SET_NULL)
    account = models.ForeignKey(BankAccount, null=True, blank=True, on_delete=models.SET_NULL)
    metadata = models.TextField(default='{}', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.action


class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=120)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class Loan(models.Model):
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='loans')
    issued_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='issued_loans')
    principal = models.DecimalField(max_digits=14, decimal_places=2)
    annual_interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    term_months = models.PositiveIntegerField()
    monthly_payment = models.DecimalField(max_digits=14, decimal_places=2)
    total_payable = models.DecimalField(max_digits=14, decimal_places=2)
    remaining_amount = models.DecimalField(max_digits=14, decimal_places=2)
    status = models.CharField(max_length=12, choices=LoanStatus.choices, default=LoanStatus.PENDING)
    purpose = models.CharField(max_length=255, blank=True)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='approved_loans')
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.CharField(max_length=255, blank=True)
    issued_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-issued_at']

    def __str__(self):
        return f'Loan #{self.id} - {self.customer.username}'


class LoanInstallment(models.Model):
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='installments')
    sequence = models.PositiveIntegerField()
    amount_due = models.DecimalField(max_digits=14, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    due_date = models.DateField()
    paid_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=12, choices=InstallmentStatus.choices, default=InstallmentStatus.PENDING)
    notified_overdue = models.BooleanField(default=False)
    transaction = models.ForeignKey(Transaction, null=True, blank=True, on_delete=models.SET_NULL, related_name='loan_installments')

    class Meta:
        ordering = ['due_date', 'sequence']
        unique_together = ('loan', 'sequence')

    def __str__(self):
        return f'Loan #{self.loan_id} installment {self.sequence}'
