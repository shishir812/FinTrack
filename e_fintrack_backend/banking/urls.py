from django.urls import path

from . import views

urlpatterns = [
    path('health/', views.HealthView.as_view()),
    path('auth/register/', views.RegisterView.as_view()),
    path('auth/login/', views.LoginView.as_view()),
    path('me/', views.MeView.as_view()),
    path('account/', views.AccountView.as_view()),
    path('accounts/', views.AccountListView.as_view()),
    path('transactions/', views.TransactionHistoryView.as_view()),
    path('transactions/deposit/', views.DepositView.as_view()),
    path('transactions/withdraw/', views.WithdrawView.as_view()),
    path('transactions/transfer/', views.TransferView.as_view()),
    path('summary/monthly/', views.SummaryView.as_view()),
    path('beneficiaries/', views.BeneficiaryListCreateView.as_view()),
    path('notifications/', views.NotificationListView.as_view()),
    path('loans/', views.LoanListView.as_view()),
    path('loans/issue/', views.LoanIssueView.as_view()),
    path('loans/pending/', views.PendingLoanListView.as_view()),
    path('loans/<int:pk>/<str:action>/', views.LoanApprovalActionView.as_view()),
    path('loans/installments/<int:pk>/pay/', views.LoanInstallmentPayView.as_view()),
    path('loans/installments/overdue/', views.OverdueInstallmentListView.as_view()),
    path('admin/transactions/pending/', views.AdminPendingTransactionsView.as_view()),
    path('admin/transactions/<int:pk>/<str:action>/', views.AdminTransactionActionView.as_view()),
    path('admin/registrations/pending/', views.AdminPendingRegistrationListView.as_view()),
    path('admin/registrations/<int:pk>/<str:action>/', views.AdminRegistrationActionView.as_view()),
    path('admin/accounts/', views.AdminAccountListView.as_view()),
    path('admin/accounts/<int:pk>/profile/', views.AdminAccountProfileUpdateView.as_view()),
    path('admin/accounts/<int:pk>/<str:action>/', views.AdminAccountStatusView.as_view()),
    path('admin/audit-logs/', views.AdminAuditLogView.as_view()),
]
