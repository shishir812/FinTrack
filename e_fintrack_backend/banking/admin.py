from django.contrib import admin
from .models import AuditLog, BankAccount, Beneficiary, Loan, LoanInstallment, Notification, Transaction, UserProfile


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = ('account_number', 'user', 'balance', 'status', 'created_at')
    search_fields = ('account_number', 'user__username', 'user__email')
    list_filter = ('status',)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'transaction_type', 'amount', 'status', 'sender', 'receiver', 'requires_approval', 'created_at')
    list_filter = ('transaction_type', 'status', 'requires_approval')
    search_fields = ('sender__account_number', 'receiver__account_number', 'created_by__username')


admin.site.register(Beneficiary)
admin.site.register(AuditLog)
admin.site.register(Notification)
admin.site.register(UserProfile)


class LoanInstallmentInline(admin.TabularInline):
    model = LoanInstallment
    extra = 0


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'principal', 'annual_interest_rate', 'term_months', 'monthly_payment', 'remaining_amount', 'status')
    list_filter = ('status',)
    search_fields = ('customer__username',)
    inlines = [LoanInstallmentInline]
