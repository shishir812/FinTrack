from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .jwt_utils import create_token
from .models import (
    AccountStatus, AuditLog, BankAccount, Beneficiary, Loan, LoanInstallment,
    Notification, RegistrationStatus, Transaction, TransactionStatus,
    UserProfile, UserRole,
)
from .serializers import (
    AddBeneficiarySerializer, AdminUserProfileUpdateSerializer,
    AuditLogSerializer, BankAccountSerializer, BeneficiarySerializer,
    LoanInstallmentSerializer, LoanIssueSerializer, LoanSerializer,
    LoginSerializer, MoneyMovementSerializer, NotificationSerializer,
    PendingRegistrationSerializer, RegisterSerializer, TransactionSerializer,
    TransferSerializer, UserSerializer,
)
from .services import (
    approve_loan, approve_transaction, can_manage_loans, create_account_for_user,
    deposit, issue_loan, monthly_summary, pay_loan_installment, reject_loan,
    reject_transaction, set_account_status, sync_overdue_installments, transfer,
    user_role, user_transactions, withdraw,
)


class RegisterView(APIView):
    def post(self, request):
        actor_role = user_role(request.user)
        if actor_role not in (UserRole.ADMIN, UserRole.EMPLOYEE):
            return Response({'detail': 'Only admins and bank employees can register users.'}, status=status.HTTP_403_FORBIDDEN)
        serializer = RegisterSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        profile = UserProfile.objects.select_related('user', 'created_by').get(user=user)
        if profile.status == RegistrationStatus.ACTIVE:
            create_account_for_user(user)
        else:
            for admin_user in get_user_model().objects.filter(is_staff=True):
                Notification.objects.create(
                    user=admin_user,
                    title='Member registration pending',
                    message=f'{request.user.username} requested member registration for {user.username}.',
                )
        return Response({'user': UserSerializer(user).data, 'profile': PendingRegistrationSerializer(profile).data}, status=status.HTTP_201_CREATED)


class HealthView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response({
            'status': 'ok',
            'service': 'FinTrack API',
            'large_transaction_limit': getattr(settings, 'FINTRACK_LARGE_TRANSACTION_LIMIT', 10000),
        })


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        return Response({'token': create_token(user), 'user': UserSerializer(user).data})


class MeView(APIView):
    def get(self, request):
        account = create_account_for_user(request.user)
        return Response({'user': UserSerializer(request.user).data, 'account': BankAccountSerializer(account).data})


class AccountView(APIView):
    def get(self, request):
        return Response(BankAccountSerializer(create_account_for_user(request.user)).data)


class AccountListView(generics.ListAPIView):
    serializer_class = BankAccountSerializer

    def get_queryset(self):
        return BankAccount.objects.select_related('user').filter(status=AccountStatus.ACTIVE).exclude(user=self.request.user)


class DepositView(APIView):
    def post(self, request):
        serializer = MoneyMovementSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        txn = deposit(request.user, serializer.validated_data['amount'], serializer.validated_data.get('description', ''))
        return Response(TransactionSerializer(txn).data, status=status.HTTP_201_CREATED)


class WithdrawView(APIView):
    def post(self, request):
        serializer = MoneyMovementSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        txn = withdraw(request.user, serializer.validated_data['amount'], serializer.validated_data.get('description', ''))
        return Response(TransactionSerializer(txn).data, status=status.HTTP_201_CREATED)


class TransferView(APIView):
    def post(self, request):
        serializer = TransferSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        receiver_identifier = serializer.validated_data.get('receiver_account_number', '')
        beneficiary_id = serializer.validated_data.get('beneficiary_id')
        if beneficiary_id is not None:
            try:
                beneficiary = request.user.beneficiaries.select_related('account').get(pk=beneficiary_id)
            except Beneficiary.DoesNotExist:
                return Response({'detail': 'Saved beneficiary not found.'}, status=status.HTTP_404_NOT_FOUND)
            receiver_identifier = beneficiary.account.account_number
        txn = transfer(
            request.user,
            receiver_identifier,
            serializer.validated_data['amount'],
            serializer.validated_data.get('description', ''),
        )
        return Response(TransactionSerializer(txn).data, status=status.HTTP_201_CREATED)


class TransactionHistoryView(generics.ListAPIView):
    serializer_class = TransactionSerializer

    def get_queryset(self):
        return user_transactions(self.request.user)


class SummaryView(APIView):
    def get(self, request):
        return Response(monthly_summary(request.user))


class BeneficiaryListCreateView(APIView):
    def get(self, request):
        return Response(BeneficiarySerializer(request.user.beneficiaries.all(), many=True).data)

    def post(self, request):
        serializer = AddBeneficiarySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        identifier = serializer.validated_data['account_number'].strip()
        try:
            account = BankAccount.objects.select_related('user').get(
                Q(account_number__iexact=identifier) | Q(user__username__iexact=identifier)
            )
        except BankAccount.DoesNotExist:
            return Response({'detail': 'Account not found.'}, status=status.HTTP_404_NOT_FOUND)
        if account.user_id == request.user.id:
            return Response({'detail': 'You cannot add your own account as a beneficiary.'}, status=status.HTTP_400_BAD_REQUEST)
        beneficiary, _ = Beneficiary.objects.get_or_create(
            owner=request.user,
            account=account,
            defaults={'nickname': serializer.validated_data.get('nickname', '')},
        )
        return Response(BeneficiarySerializer(beneficiary).data, status=status.HTTP_201_CREATED)


class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)


class LoanListView(generics.ListAPIView):
    serializer_class = LoanSerializer

    def get_queryset(self):
        sync_overdue_installments()
        queryset = Loan.objects.select_related('customer', 'issued_by').prefetch_related('installments')
        if can_manage_loans(self.request.user):
            return queryset
        return queryset.filter(customer=self.request.user)


class LoanIssueView(APIView):
    def post(self, request):
        if not can_manage_loans(request.user):
            return Response({'detail': 'Only admins and bank employees can issue loans.'}, status=status.HTTP_403_FORBIDDEN)
        serializer = LoanIssueSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        identifier = serializer.validated_data['customer'].strip()
        try:
            account = BankAccount.objects.select_related('user').get(
                Q(account_number__iexact=identifier) | Q(user__username__iexact=identifier)
            )
        except BankAccount.DoesNotExist:
            return Response({'detail': 'Customer not found.'}, status=status.HTTP_404_NOT_FOUND)
        try:
            loan = issue_loan(
                request.user,
                account.user,
                serializer.validated_data['principal'],
                serializer.validated_data['annual_interest_rate'],
                serializer.validated_data['term_months'],
                serializer.validated_data.get('purpose', ''),
            )
        except (PermissionError, ValueError) as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(LoanSerializer(loan).data, status=status.HTTP_201_CREATED)


class PendingLoanListView(generics.ListAPIView):
    serializer_class = LoanSerializer

    def get_queryset(self):
        if user_role(self.request.user) != UserRole.ADMIN:
            return Loan.objects.none()
        return Loan.objects.select_related('customer', 'issued_by').prefetch_related('installments').filter(status='PENDING')


class LoanApprovalActionView(APIView):
    def post(self, request, pk, action):
        if user_role(request.user) != UserRole.ADMIN:
            return Response({'detail': 'Only admins can approve or reject loans.'}, status=status.HTTP_403_FORBIDDEN)
        try:
            if action == 'approve':
                loan = approve_loan(request.user, pk)
            elif action == 'reject':
                loan = reject_loan(request.user, pk, request.data.get('reason', 'Rejected by admin.'))
            else:
                return Response({'detail': 'Unknown action.'}, status=status.HTTP_400_BAD_REQUEST)
        except Loan.DoesNotExist:
            return Response({'detail': 'Pending loan not found.'}, status=status.HTTP_404_NOT_FOUND)
        except (PermissionError, ValueError) as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(LoanSerializer(loan).data)


class LoanInstallmentPayView(APIView):
    def post(self, request, pk):
        try:
            installment = pay_loan_installment(request.user, pk)
        except LoanInstallment.DoesNotExist:
            return Response({'detail': 'Installment not found.'}, status=status.HTTP_404_NOT_FOUND)
        except PermissionError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_403_FORBIDDEN)
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(LoanInstallmentSerializer(installment).data)


class OverdueInstallmentListView(generics.ListAPIView):
    serializer_class = LoanInstallmentSerializer

    def get_queryset(self):
        if not can_manage_loans(self.request.user):
            return LoanInstallment.objects.none()
        sync_overdue_installments()
        return LoanInstallment.objects.select_related('loan', 'loan__customer').filter(status='OVERDUE')


class AdminPendingTransactionsView(generics.ListAPIView):
    permission_classes = [permissions.IsAdminUser]
    serializer_class = TransactionSerializer
    queryset = Transaction.objects.filter(status=TransactionStatus.PENDING)


class AdminTransactionActionView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, pk, action):
        if action == 'approve':
            txn = approve_transaction(request.user, pk)
        elif action == 'reject':
            txn = reject_transaction(request.user, pk, request.data.get('reason', 'Rejected by admin.'))
        else:
            return Response({'detail': 'Unknown action.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(TransactionSerializer(txn).data)


class AdminAccountListView(generics.ListAPIView):
    permission_classes = [permissions.IsAdminUser]
    serializer_class = BankAccountSerializer

    def get_queryset(self):
        admin_user = get_user_model().objects.filter(Q(is_staff=True) | Q(profile__role=UserRole.ADMIN)).order_by('id').first()
        admin_filter = Q(user__is_staff=True) | Q(user__profile__role=UserRole.ADMIN)
        queryset = BankAccount.objects.select_related('user', 'user__profile').all()
        if not admin_user:
            return queryset
        return queryset.filter(Q(user_id=admin_user.id) | ~admin_filter).distinct()


class AdminAccountStatusView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, pk, action):
        if action == 'freeze':
            account = set_account_status(request.user, pk, AccountStatus.FROZEN)
        elif action == 'unfreeze':
            account = set_account_status(request.user, pk, AccountStatus.ACTIVE)
        else:
            return Response({'detail': 'Unknown action.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(BankAccountSerializer(account).data)


class AdminAccountProfileUpdateView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def patch(self, request, pk):
        try:
            account = BankAccount.objects.select_related('user', 'user__profile').get(pk=pk)
        except BankAccount.DoesNotExist:
            return Response({'detail': 'Account not found.'}, status=status.HTTP_404_NOT_FOUND)

        target_user = account.user
        if target_user.is_staff or user_role(target_user) == UserRole.ADMIN:
            return Response({'detail': 'Admin profiles cannot be edited here.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = AdminUserProfileUpdateSerializer(target_user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        account.refresh_from_db()
        return Response(BankAccountSerializer(account).data)


class AdminPendingRegistrationListView(generics.ListAPIView):
    permission_classes = [permissions.IsAdminUser]
    serializer_class = PendingRegistrationSerializer
    queryset = UserProfile.objects.select_related('user', 'created_by').filter(status=RegistrationStatus.PENDING)


class AdminRegistrationActionView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, pk, action):
        try:
            profile = UserProfile.objects.select_related('user', 'created_by').get(pk=pk, status=RegistrationStatus.PENDING)
        except UserProfile.DoesNotExist:
            return Response({'detail': 'Pending registration not found.'}, status=status.HTTP_404_NOT_FOUND)

        if action == 'approve':
            profile.status = RegistrationStatus.ACTIVE
            profile.approved_by = request.user
            profile.approved_at = timezone.now()
            profile.rejection_reason = ''
            profile.save(update_fields=['status', 'approved_by', 'approved_at', 'rejection_reason'])
            create_account_for_user(profile.user)
            Notification.objects.create(
                user=profile.user,
                title='Account approved',
                message='Your member account has been approved by admin.',
            )
            if profile.created_by:
                Notification.objects.create(
                    user=profile.created_by,
                    title='Member registration approved',
                    message=f'{profile.user.username} is now an active member.',
                )
        elif action == 'reject':
            profile.status = RegistrationStatus.REJECTED
            profile.rejection_reason = request.data.get('reason', 'Rejected by admin.')
            profile.approved_by = request.user
            profile.approved_at = timezone.now()
            profile.save(update_fields=['status', 'rejection_reason', 'approved_by', 'approved_at'])
            Notification.objects.create(
                user=profile.user,
                title='Account registration rejected',
                message=profile.rejection_reason,
            )
            if profile.created_by:
                Notification.objects.create(
                    user=profile.created_by,
                    title='Member registration rejected',
                    message=f'{profile.user.username} was rejected by admin.',
                )
        else:
            return Response({'detail': 'Unknown action.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(PendingRegistrationSerializer(profile).data)


class AdminAuditLogView(generics.ListAPIView):
    permission_classes = [permissions.IsAdminUser]
    serializer_class = AuditLogSerializer
    queryset = AuditLog.objects.all()
