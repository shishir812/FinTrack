import json
from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from .models import (
    AccountStatus, AuditLog, BankAccount, InstallmentStatus, Loan, LoanInstallment,
    LoanStatus, Notification, Transaction, TransactionStatus, TransactionType, UserProfile,
    UserRole,
)


def _create_individual_account(user):
    account_number = f'FT{user.id:08d}'
    account, _ = BankAccount.objects.get_or_create(user=user, defaults={'account_number': account_number})
    role = UserRole.ADMIN if user.is_staff else UserRole.CUSTOMER
    UserProfile.objects.get_or_create(user=user, defaults={'role': role})
    return account


def create_account_for_user(user):
    account = _create_individual_account(user)
    if user_role(user) == UserRole.ADMIN:
        return _primary_admin_account()
    return account


def user_role(user):
    if user.is_staff:
        return UserRole.ADMIN
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile.role


def can_manage_loans(user):
    return user_role(user) in {UserRole.ADMIN, UserRole.EMPLOYEE}


def user_transactions(user):
    account = create_account_for_user(user)
    return Transaction.objects.filter(Q(sender=account) | Q(receiver=account) | Q(created_by=user)).distinct()


def monthly_summary(user):
    account = create_account_for_user(user)
    txns = user_transactions(user).filter(status=TransactionStatus.SUCCESS)
    summary = {}
    for tx in txns:
        key = tx.created_at.strftime('%Y-%m')
        item = summary.setdefault(key, {'month': key, 'income': Decimal('0'), 'expense': Decimal('0')})
        if tx.receiver_id == account.id:
            item['income'] += tx.amount
        if tx.sender_id == account.id:
            item['expense'] += tx.amount
    return list(summary.values())[-6:]


def _audit(actor, action, account=None, txn=None, **metadata):
    AuditLog.objects.create(actor=actor, action=action, account=account, transaction=txn, metadata=json.dumps(metadata))


def _notify(user, title, message):
    Notification.objects.create(user=user, title=title, message=message)


def _is_large(amount):
    return amount >= Decimal(str(getattr(settings, 'FINTRACK_LARGE_TRANSACTION_LIMIT', 10000)))


def _ensure_active(account):
    if account.status != AccountStatus.ACTIVE:
        raise ValueError('Account is not active.')


def _admin_users():
    User = get_user_model()
    return User.objects.filter(Q(is_staff=True) | Q(profile__role=UserRole.ADMIN)).distinct()


def _primary_admin_account():
    admin = _admin_users().order_by('id').first()
    if not admin:
        raise ValueError('No admin account is available for bank deposits.')
    return _create_individual_account(admin)


def _is_employee_created_transaction(txn):
    return bool(txn.created_by_id and user_role(txn.created_by) == UserRole.EMPLOYEE)


@transaction.atomic
def deposit(user, amount, description=''):
    employee_deposit = user_role(user) == UserRole.EMPLOYEE
    user_account = _primary_admin_account() if employee_deposit else create_account_for_user(user)
    account = BankAccount.objects.select_for_update().get(pk=user_account.pk)
    if account.status != AccountStatus.ACTIVE:
        txn = Transaction.objects.create(
            transaction_type=TransactionType.DEPOSIT, amount=amount, receiver=account,
            status=TransactionStatus.FAILED, failure_reason='Account is not active.',
            description=description, created_by=user,
        )
        _audit(user, 'DEPOSIT_FAILED', account, txn, reason='Account inactive')
        return txn
    if employee_deposit or _is_large(amount):
        txn = Transaction.objects.create(
            transaction_type=TransactionType.DEPOSIT, amount=amount, receiver=account,
            status=TransactionStatus.PENDING, requires_approval=True,
            description=description, created_by=user,
        )
        _audit(user, 'DEPOSIT_PENDING_APPROVAL', account, txn)
        if employee_deposit:
            for admin in _admin_users():
                _notify(admin, 'Employee deposit pending approval', f'{user.username} submitted a bank deposit of {amount} for approval.')
        return txn
    account.balance += amount
    account.save(update_fields=['balance', 'updated_at'])
    txn = Transaction.objects.create(
        transaction_type=TransactionType.DEPOSIT, amount=amount, receiver=account,
        status=TransactionStatus.SUCCESS, description=description, created_by=user,
    )
    _audit(user, 'DEPOSIT_SUCCESS', account, txn)
    if employee_deposit:
        for admin in _admin_users():
            _notify(admin, 'Employee deposit received', f'{user.username} deposited {amount} into the bank admin account.')
    return txn


@transaction.atomic
def withdraw(user, amount, description=''):
    user_account = create_account_for_user(user)
    account = BankAccount.objects.select_for_update().get(pk=user_account.pk)
    txn = Transaction.objects.create(
        transaction_type=TransactionType.WITHDRAWAL, amount=amount, sender=account,
        description=description, created_by=user,
    )
    if account.status != AccountStatus.ACTIVE:
        txn.status = TransactionStatus.FAILED
        txn.failure_reason = 'Account is not active.'
        txn.save(update_fields=['status', 'failure_reason', 'updated_at'])
        _audit(user, 'WITHDRAWAL_FAILED', account, txn, reason=txn.failure_reason)
        return txn
    if account.balance < amount:
        txn.status = TransactionStatus.FAILED
        txn.failure_reason = 'Insufficient balance.'
        txn.save(update_fields=['status', 'failure_reason', 'updated_at'])
        _audit(user, 'WITHDRAWAL_FAILED', account, txn, reason=txn.failure_reason)
        return txn
    if _is_large(amount):
        txn.requires_approval = True
        txn.status = TransactionStatus.PENDING
        txn.save(update_fields=['requires_approval', 'status', 'updated_at'])
        _audit(user, 'WITHDRAWAL_PENDING_APPROVAL', account, txn)
        return txn
    account.balance -= amount
    account.save(update_fields=['balance', 'updated_at'])
    txn.status = TransactionStatus.SUCCESS
    txn.save(update_fields=['status', 'updated_at'])
    _audit(user, 'WITHDRAWAL_SUCCESS', account, txn)
    return txn


@transaction.atomic
def transfer(user, receiver_account_number, amount, description=''):
    user_account = create_account_for_user(user)
    sender = BankAccount.objects.select_for_update().get(pk=user_account.pk)
    receiver_identifier = str(receiver_account_number).strip()
    try:
        receiver = (
            BankAccount.objects.select_for_update()
            .select_related('user')
            .get(Q(account_number__iexact=receiver_identifier) | Q(user__username__iexact=receiver_identifier))
        )
    except BankAccount.DoesNotExist:
        txn = Transaction.objects.create(
            transaction_type=TransactionType.TRANSFER, amount=amount, sender=sender,
            status=TransactionStatus.FAILED, failure_reason='Receiver account not found.',
            description=description, created_by=user,
        )
        _audit(user, 'TRANSFER_FAILED', sender, txn, reason=txn.failure_reason)
        return txn
    txn = Transaction.objects.create(
        transaction_type=TransactionType.TRANSFER, amount=amount, sender=sender, receiver=receiver,
        description=description, created_by=user,
    )
    if sender.pk == receiver.pk:
        txn.status = TransactionStatus.FAILED
        txn.failure_reason = 'Cannot transfer to the same account.'
    elif sender.status != AccountStatus.ACTIVE or receiver.status != AccountStatus.ACTIVE:
        txn.status = TransactionStatus.FAILED
        txn.failure_reason = 'Both accounts must be active.'
    elif sender.balance < amount:
        txn.status = TransactionStatus.FAILED
        txn.failure_reason = 'Insufficient balance.'
    elif _is_large(amount):
        txn.status = TransactionStatus.PENDING
        txn.requires_approval = True
    else:
        sender.balance -= amount
        receiver.balance += amount
        sender.save(update_fields=['balance', 'updated_at'])
        receiver.save(update_fields=['balance', 'updated_at'])
        txn.status = TransactionStatus.SUCCESS
    txn.save(update_fields=['status', 'failure_reason', 'requires_approval', 'updated_at'])
    _audit(user, f'TRANSFER_{txn.status}', sender, txn, receiver=receiver.account_number)
    if txn.status == TransactionStatus.SUCCESS:
        _notify(receiver.user, 'Incoming transfer', f'{user.username} sent {amount}.')
    return txn


@transaction.atomic
def approve_transaction(admin_user, transaction_id):
    txn = Transaction.objects.select_for_update().get(pk=transaction_id, status=TransactionStatus.PENDING)
    if txn.transaction_type == TransactionType.DEPOSIT:
        receiver_account = _primary_admin_account() if _is_employee_created_transaction(txn) else txn.receiver
        receiver = BankAccount.objects.select_for_update().get(pk=receiver_account.pk)
        _ensure_active(receiver)
        receiver.balance += txn.amount
        receiver.save(update_fields=['balance', 'updated_at'])
        if txn.receiver_id != receiver.id:
            txn.receiver = receiver
            txn.save(update_fields=['receiver', 'updated_at'])
    elif txn.transaction_type == TransactionType.WITHDRAWAL:
        sender = BankAccount.objects.select_for_update().get(pk=txn.sender_id)
        _ensure_active(sender)
        if sender.balance < txn.amount:
            txn.status = TransactionStatus.FAILED
            txn.failure_reason = 'Insufficient balance at approval time.'
            txn.approved_by = admin_user
            txn.approved_at = timezone.now()
            txn.save(update_fields=['status', 'failure_reason', 'approved_by', 'approved_at', 'updated_at'])
            _audit(admin_user, 'TRANSACTION_APPROVAL_FAILED', sender, txn)
            return txn
        sender.balance -= txn.amount
        sender.save(update_fields=['balance', 'updated_at'])
    elif txn.transaction_type == TransactionType.TRANSFER:
        sender = BankAccount.objects.select_for_update().get(pk=txn.sender_id)
        receiver = BankAccount.objects.select_for_update().get(pk=txn.receiver_id)
        _ensure_active(sender)
        _ensure_active(receiver)
        if sender.balance < txn.amount:
            txn.status = TransactionStatus.FAILED
            txn.failure_reason = 'Insufficient balance at approval time.'
            txn.approved_by = admin_user
            txn.approved_at = timezone.now()
            txn.save(update_fields=['status', 'failure_reason', 'approved_by', 'approved_at', 'updated_at'])
            _audit(admin_user, 'TRANSACTION_APPROVAL_FAILED', sender, txn)
            return txn
        sender.balance -= txn.amount
        receiver.balance += txn.amount
        sender.save(update_fields=['balance', 'updated_at'])
        receiver.save(update_fields=['balance', 'updated_at'])
    txn.mark_success(admin_user)
    _audit(admin_user, 'TRANSACTION_APPROVED', txn.sender or txn.receiver, txn)
    return txn


@transaction.atomic
def reject_transaction(admin_user, transaction_id, reason='Rejected by admin.'):
    txn = Transaction.objects.select_for_update().get(pk=transaction_id, status=TransactionStatus.PENDING)
    txn.status = TransactionStatus.REJECTED
    txn.failure_reason = reason
    txn.approved_by = admin_user
    txn.approved_at = timezone.now()
    txn.save(update_fields=['status', 'failure_reason', 'approved_by', 'approved_at', 'updated_at'])
    _audit(admin_user, 'TRANSACTION_REJECTED', txn.sender or txn.receiver, txn, reason=reason)
    return txn


@transaction.atomic
def set_account_status(admin_user, account_id, status):
    account = BankAccount.objects.select_for_update().get(pk=account_id)
    account.status = status
    account.save(update_fields=['status', 'updated_at'])
    _audit(admin_user, f'ACCOUNT_{status}', account)
    return account


def _money(value):
    return Decimal(value).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def _create_loan_installments(loan):
    if loan.installments.exists():
        return
    today = timezone.localdate()
    for index in range(1, loan.term_months + 1):
        amount_due = loan.monthly_payment if index < loan.term_months else _money(loan.total_payable - loan.monthly_payment * Decimal(loan.term_months - 1))
        LoanInstallment.objects.create(
            loan=loan,
            sequence=index,
            amount_due=amount_due,
            due_date=today + timedelta(days=30 * index),
        )


def _disburse_approved_loan(loan, admin_user):
    account = BankAccount.objects.select_for_update().get(pk=create_account_for_user(loan.customer).pk)
    if account.status != AccountStatus.ACTIVE:
        raise ValueError('Customer account is not active.')
    _create_loan_installments(loan)
    account.balance += loan.principal
    account.save(update_fields=['balance', 'updated_at'])
    loan.status = LoanStatus.ACTIVE
    loan.approved_by = admin_user
    loan.approved_at = timezone.now()
    loan.rejection_reason = ''
    loan.save(update_fields=['status', 'approved_by', 'approved_at', 'rejection_reason', 'updated_at'])
    txn = Transaction.objects.create(
        transaction_type=TransactionType.LOAN_ISSUE,
        amount=loan.principal,
        receiver=account,
        status=TransactionStatus.SUCCESS,
        description=f'Loan disbursement #{loan.id}',
        created_by=admin_user,
    )
    _audit(admin_user, 'LOAN_APPROVED_AND_DISBURSED', account, txn, loan_id=loan.id, customer=loan.customer.username)
    _notify(loan.customer, 'Loan approved', f'Your loan #{loan.id} was approved. Monthly payment: {loan.monthly_payment}.')
    return loan


@transaction.atomic
def issue_loan(actor, customer, principal, annual_interest_rate, term_months, purpose=''):
    if not can_manage_loans(actor):
        raise PermissionError('Only admins and bank employees can issue loans.')
    if user_role(customer) != UserRole.CUSTOMER:
        raise ValueError('Loans can only be issued to customers.')
    if term_months < 1:
        raise ValueError('Loan term must be at least 1 month.')

    account = BankAccount.objects.select_for_update().get(pk=create_account_for_user(customer).pk)
    if account.status != AccountStatus.ACTIVE:
        raise ValueError('Customer account is not active.')

    principal = _money(principal)
    annual_interest_rate = _money(annual_interest_rate)
    months = Decimal(term_months)
    total_interest = _money(principal * (annual_interest_rate / Decimal('100')) * (months / Decimal('12')))
    total_payable = _money(principal + total_interest)
    monthly_payment = _money(total_payable / months)

    loan = Loan.objects.create(
        customer=customer,
        issued_by=actor,
        principal=principal,
        annual_interest_rate=annual_interest_rate,
        term_months=term_months,
        monthly_payment=monthly_payment,
        total_payable=total_payable,
        remaining_amount=total_payable,
        status=LoanStatus.PENDING,
        purpose=purpose,
    )

    _audit(actor, 'LOAN_REQUESTED', account, None, loan_id=loan.id, customer=customer.username)
    _notify(customer, 'Loan requested', f'Loan #{loan.id} was requested and is waiting for admin approval.')
    if user_role(actor) == UserRole.ADMIN:
        return _disburse_approved_loan(loan, actor)
    return loan


@transaction.atomic
def approve_loan(admin_user, loan_id):
    if user_role(admin_user) != UserRole.ADMIN:
        raise PermissionError('Only admins can approve loans.')
    loan = Loan.objects.select_for_update().select_related('customer').get(pk=loan_id, status=LoanStatus.PENDING)
    return _disburse_approved_loan(loan, admin_user)


@transaction.atomic
def reject_loan(admin_user, loan_id, reason='Rejected by admin.'):
    if user_role(admin_user) != UserRole.ADMIN:
        raise PermissionError('Only admins can reject loans.')
    loan = Loan.objects.select_for_update().select_related('customer').get(pk=loan_id, status=LoanStatus.PENDING)
    loan.status = LoanStatus.REJECTED
    loan.approved_by = admin_user
    loan.approved_at = timezone.now()
    loan.rejection_reason = reason
    loan.save(update_fields=['status', 'approved_by', 'approved_at', 'rejection_reason', 'updated_at'])
    _audit(admin_user, 'LOAN_REJECTED', create_account_for_user(loan.customer), None, loan_id=loan.id, reason=reason)
    _notify(loan.customer, 'Loan rejected', f'Loan #{loan.id} was rejected. {reason}')
    return loan


@transaction.atomic
def pay_loan_installment(user, installment_id):
    installment = LoanInstallment.objects.select_for_update().select_related('loan', 'loan__customer').get(pk=installment_id)
    if installment.loan.customer_id != user.id:
        raise PermissionError('You can only pay your own loan installments.')
    if installment.loan.status != LoanStatus.ACTIVE:
        raise ValueError('Only active loans can be paid.')
    if installment.status == InstallmentStatus.PAID:
        raise ValueError('This installment is already paid.')

    account = BankAccount.objects.select_for_update().get(pk=create_account_for_user(user).pk)
    if account.status != AccountStatus.ACTIVE:
        raise ValueError('Account is not active.')
    if account.balance < installment.amount_due:
        raise ValueError('Insufficient balance to pay this installment.')

    account.balance -= installment.amount_due
    account.save(update_fields=['balance', 'updated_at'])
    loan = installment.loan
    loan.remaining_amount = _money(max(Decimal('0.00'), loan.remaining_amount - installment.amount_due))
    if loan.remaining_amount == Decimal('0.00'):
        loan.status = LoanStatus.PAID
    loan.save(update_fields=['remaining_amount', 'status', 'updated_at'])

    txn = Transaction.objects.create(
        transaction_type=TransactionType.LOAN_PAYMENT,
        amount=installment.amount_due,
        sender=account,
        status=TransactionStatus.SUCCESS,
        description=f'Loan #{loan.id} installment {installment.sequence}',
        created_by=user,
    )
    installment.amount_paid = installment.amount_due
    installment.status = InstallmentStatus.PAID
    installment.paid_at = timezone.now()
    installment.transaction = txn
    installment.save(update_fields=['amount_paid', 'status', 'paid_at', 'transaction'])
    _audit(user, 'LOAN_INSTALLMENT_PAID', account, txn, loan_id=loan.id, installment_id=installment.id)
    return installment


def sync_overdue_installments():
    today = timezone.localdate()
    overdue = LoanInstallment.objects.select_related('loan', 'loan__customer').filter(
        loan__status=LoanStatus.ACTIVE,
        status=InstallmentStatus.PENDING,
        due_date__lt=today,
    )
    changed = []
    for installment in overdue:
        installment.status = InstallmentStatus.OVERDUE
        if not installment.notified_overdue:
            _notify(
                installment.loan.customer,
                'Loan payment overdue',
                f'Loan #{installment.loan_id} installment {installment.sequence} was due on {installment.due_date}.',
            )
            installment.notified_overdue = True
        installment.save(update_fields=['status', 'notified_overdue'])
        changed.append(installment)
    return changed
