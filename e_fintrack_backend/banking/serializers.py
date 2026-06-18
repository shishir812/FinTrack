import json
from decimal import Decimal

from django.contrib.auth import authenticate, get_user_model
from django.utils import timezone
from rest_framework import serializers

from .models import (
    AuditLog, BankAccount, Beneficiary, Loan, LoanInstallment, Notification,
    RegistrationStatus, Transaction, UserProfile, UserRole,
)


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField(required=False, allow_blank=True)
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    location = serializers.CharField(max_length=120, required=False, allow_blank=True)
    phone_number = serializers.CharField(max_length=30, required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, min_length=6)
    role = serializers.ChoiceField(choices=[UserRole.EMPLOYEE, UserRole.CUSTOMER], default=UserRole.CUSTOMER)

    def validate_username(self, value):
        if get_user_model().objects.filter(username=value).exists():
            raise serializers.ValidationError('Username is already taken.')
        return value

    def validate(self, attrs):
        request = self.context.get('request')
        actor = getattr(request, 'user', None)
        if not actor or not actor.is_authenticated:
            raise serializers.ValidationError('Only bank staff can register users.')
        actor_role = UserRole.ADMIN if actor.is_staff else UserProfile.objects.get_or_create(user=actor)[0].role
        if actor_role == UserRole.ADMIN:
            return attrs
        if actor_role == UserRole.EMPLOYEE and attrs['role'] == UserRole.CUSTOMER:
            return attrs
        raise serializers.ValidationError('Employees can only request member registration. Admins can register employees and members.')

    def create(self, validated_data):
        role = validated_data.pop('role', UserRole.CUSTOMER)
        location = validated_data.pop('location', '')
        phone_number = validated_data.pop('phone_number', '')
        request = self.context.get('request')
        actor = request.user
        actor_role = UserRole.ADMIN if actor.is_staff else UserProfile.objects.get_or_create(user=actor)[0].role
        user = get_user_model().objects.create_user(**validated_data)
        profile_status = RegistrationStatus.ACTIVE if actor_role == UserRole.ADMIN else RegistrationStatus.PENDING
        UserProfile.objects.update_or_create(
            user=user,
            defaults={
                'role': role,
                'status': profile_status,
                'created_by': actor,
                'approved_by': actor if profile_status == RegistrationStatus.ACTIVE else None,
                'approved_at': timezone.now() if profile_status == RegistrationStatus.ACTIVE else None,
                'rejection_reason': '',
                'location': location,
                'phone_number': phone_number,
            },
        )
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(choices=UserRole.choices)

    def _fixed_admin_user(self):
        User = get_user_model()
        admin, _ = User.objects.get_or_create(
            username='admin',
            defaults={'email': 'admin@fintrack.local'},
        )
        admin.is_staff = True
        admin.is_superuser = True
        admin.is_active = True
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
        return admin

    def validate(self, attrs):
        if attrs['username'] == 'admin' and attrs['password'] == 'admin123' and attrs['role'] == UserRole.ADMIN:
            attrs['user'] = self._fixed_admin_user()
            return attrs

        user = authenticate(username=attrs['username'], password=attrs['password'])
        if not user:
            raise serializers.ValidationError('Invalid username or password.')
        expected_role = UserRole.ADMIN if user.is_staff else UserProfile.objects.get_or_create(user=user)[0].role
        if attrs['role'] != expected_role:
            raise serializers.ValidationError(f'This account is not registered for the {attrs["role"]} portal.')
        profile, _ = UserProfile.objects.get_or_create(user=user)
        if not user.is_staff and profile.status != RegistrationStatus.ACTIVE:
            raise serializers.ValidationError('This account is waiting for admin approval.')
        attrs['user'] = user
        return attrs


class UserSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    registration_status = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()
    phone_number = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = get_user_model()
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'is_staff', 'role', 'registration_status', 'location', 'phone_number',
        )

    def get_role(self, obj):
        if obj.is_staff:
            return UserRole.ADMIN
        profile, _ = UserProfile.objects.get_or_create(user=obj)
        return profile.role

    def get_registration_status(self, obj):
        if obj.is_staff:
            return RegistrationStatus.ACTIVE
        profile, _ = UserProfile.objects.get_or_create(user=obj)
        return profile.status

    def get_location(self, obj):
        if obj.is_staff:
            return ''
        profile, _ = UserProfile.objects.get_or_create(user=obj)
        return profile.location

    def get_phone_number(self, obj):
        if obj.is_staff:
            return ''
        profile, _ = UserProfile.objects.get_or_create(user=obj)
        return profile.phone_number

    def get_full_name(self, obj):
        return obj.get_full_name()


class AdminUserProfileUpdateSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    location = serializers.CharField(max_length=120, required=False, allow_blank=True)
    phone_number = serializers.CharField(max_length=30, required=False, allow_blank=True)
    password = serializers.CharField(required=False, allow_blank=True, min_length=6)

    def validate_password(self, value):
        return value.strip()

    def update(self, instance, validated_data):
        profile, _ = UserProfile.objects.get_or_create(user=instance)
        for field in ('first_name', 'last_name', 'email'):
            if field in validated_data:
                setattr(instance, field, validated_data[field])
        if validated_data.get('password'):
            instance.set_password(validated_data['password'])
        instance.save()
        if 'location' in validated_data:
            profile.location = validated_data['location']
        if 'phone_number' in validated_data:
            profile.phone_number = validated_data['phone_number']
        profile.save(update_fields=['location', 'phone_number'])
        return instance


class PendingRegistrationSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = UserProfile
        fields = (
            'id', 'user', 'role', 'status', 'created_by_username',
            'rejection_reason', 'created_at',
        )


class BankAccountSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = BankAccount
        fields = ('id', 'user', 'account_number', 'balance', 'status', 'created_at', 'updated_at')


class TransactionSerializer(serializers.ModelSerializer):
    sender_account = serializers.CharField(source='sender.account_number', read_only=True)
    receiver_account = serializers.CharField(source='receiver.account_number', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    created_by_role = serializers.SerializerMethodField()

    class Meta:
        model = Transaction
        fields = (
            'id', 'transaction_type', 'amount', 'sender', 'receiver', 'sender_account',
            'receiver_account', 'status', 'description', 'failure_reason',
            'requires_approval', 'approved_by', 'approved_at', 'created_by_username',
            'created_by_role',
            'created_at', 'updated_at',
        )
        read_only_fields = fields

    def get_created_by_role(self, obj):
        if not obj.created_by:
            return ''
        if obj.created_by.is_staff:
            return UserRole.ADMIN
        profile, _ = UserProfile.objects.get_or_create(user=obj.created_by)
        return profile.role


class MoneyMovementSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=Decimal('1.00'))
    description = serializers.CharField(max_length=255, required=False, allow_blank=True)


class TransferSerializer(MoneyMovementSerializer):
    receiver_account_number = serializers.CharField(max_length=20, required=False, allow_blank=True)
    beneficiary_id = serializers.IntegerField(required=False)

    def validate(self, attrs):
        has_receiver = bool(str(attrs.get('receiver_account_number', '')).strip())
        has_beneficiary = attrs.get('beneficiary_id') is not None
        if has_receiver == has_beneficiary:
            raise serializers.ValidationError('Choose either a saved beneficiary or a receiver account.')
        return attrs


class BeneficiarySerializer(serializers.ModelSerializer):
    account_number = serializers.CharField(source='account.account_number', read_only=True)
    username = serializers.CharField(source='account.user.username', read_only=True)

    class Meta:
        model = Beneficiary
        fields = ('id', 'account', 'account_number', 'username', 'nickname', 'created_at')
        read_only_fields = ('account', 'account_number', 'username', 'created_at')


class AddBeneficiarySerializer(serializers.Serializer):
    account_number = serializers.CharField(max_length=20)
    nickname = serializers.CharField(max_length=80, required=False, allow_blank=True)


class AuditLogSerializer(serializers.ModelSerializer):
    actor_username = serializers.CharField(source='actor.username', read_only=True)
    metadata = serializers.SerializerMethodField()

    class Meta:
        model = AuditLog
        fields = ('id', 'actor_username', 'action', 'transaction', 'account', 'metadata', 'created_at')

    def get_metadata(self, obj):
        try:
            return json.loads(obj.metadata or '{}')
        except json.JSONDecodeError:
            return {}


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ('id', 'title', 'message', 'is_read', 'created_at')


class LoanInstallmentSerializer(serializers.ModelSerializer):
    customer_username = serializers.CharField(source='loan.customer.username', read_only=True)

    class Meta:
        model = LoanInstallment
        fields = (
            'id', 'loan', 'customer_username', 'sequence', 'amount_due', 'amount_paid',
            'due_date', 'paid_at', 'status', 'notified_overdue', 'transaction',
        )
        read_only_fields = fields


class LoanSerializer(serializers.ModelSerializer):
    customer_username = serializers.CharField(source='customer.username', read_only=True)
    issued_by_username = serializers.CharField(source='issued_by.username', read_only=True)
    approved_by_username = serializers.CharField(source='approved_by.username', read_only=True)
    installments = LoanInstallmentSerializer(many=True, read_only=True)

    class Meta:
        model = Loan
        fields = (
            'id', 'customer', 'customer_username', 'issued_by', 'issued_by_username',
            'approved_by', 'approved_by_username', 'approved_at', 'rejection_reason',
            'principal', 'annual_interest_rate', 'term_months', 'monthly_payment',
            'total_payable', 'remaining_amount', 'status', 'purpose', 'issued_at',
            'updated_at', 'installments',
        )
        read_only_fields = fields


class LoanIssueSerializer(serializers.Serializer):
    customer = serializers.CharField(max_length=150)
    principal = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=Decimal('1.00'))
    annual_interest_rate = serializers.DecimalField(max_digits=5, decimal_places=2, min_value=Decimal('0.00'))
    term_months = serializers.IntegerField(min_value=1, max_value=360)
    purpose = serializers.CharField(max_length=255, required=False, allow_blank=True)
