import { useEffect, useMemo, useState } from 'react';
import { Alert, ConfigProvider, Form, Tag, theme } from 'antd';

import AuthPage from './components/auth/AuthPage';
import AppShell from './components/layout/AppShell';
import AdminApprovalsSection from './components/sections/AdminApprovalsSection';
import BeneficiariesSection from './components/sections/BeneficiariesSection';
import DashboardSection from './components/sections/DashboardSection';
import LoansSection from './components/sections/LoansSection';
import MoneySection from './components/sections/MoneySection';
import MonthlySummaryCard from './components/sections/MonthlySummaryCard';
import NotificationsSection from './components/sections/NotificationsSection';
import TransactionHistorySection from './components/sections/TransactionHistorySection';
import UserRegistrationSection from './components/sections/UserRegistrationSection';
import { API_URL, ROLE_OPTIONS } from './config';
import { matchesSearch, money, statusColor } from './utils/formatters';
import { canManageLoans as canManageLoansFor, isAdminUser } from './utils/roles';

const themeConfig = {
  algorithm: theme.defaultAlgorithm,
  token: {
    colorPrimary: '#0e5e59',
    borderRadius: 8,
  },
};

const loanSearchFields = [
  'id',
  'customer_username',
  'principal',
  'monthly_payment',
  'remaining_amount',
  'status',
  'purpose',
  'issued_by_username',
  'approved_by_username',
];

const transactionSearchFields = [
  'transaction_type',
  'amount',
  'status',
  'sender_account',
  'receiver_account',
  'description',
  'failure_reason',
  'created_by_username',
  'created_by_role',
  'created_at',
];

export default function App() {
  const [loginForm] = Form.useForm();
  const [token, setToken] = useState(localStorage.getItem('fintrack_token') || '');
  const [user, setUser] = useState(null);
  const [account, setAccount] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [summary, setSummary] = useState([]);
  const [receiverAccounts, setReceiverAccounts] = useState([]);
  const [beneficiaries, setBeneficiaries] = useState([]);
  const [loans, setLoans] = useState([]);
  const [pendingLoans, setPendingLoans] = useState([]);
  const [overdueInstallments, setOverdueInstallments] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [pendingRegistrations, setPendingRegistrations] = useState([]);
  const [pending, setPending] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState('success');
  const [approvalLimit, setApprovalLimit] = useState(10000);
  const [authBusy, setAuthBusy] = useState(false);
  const [authRole, setAuthRole] = useState('CUSTOMER');
  const [beneficiarySearch, setBeneficiarySearch] = useState('');
  const [loanSearch, setLoanSearch] = useState('');
  const [loanApprovalSearch, setLoanApprovalSearch] = useState('');
  const [overdueSearch, setOverdueSearch] = useState('');
  const [notificationSearch, setNotificationSearch] = useState('');
  const [transactionSearch, setTransactionSearch] = useState('');
  const [adminApprovalSearch, setAdminApprovalSearch] = useState('');
  const [accountSearch, setAccountSearch] = useState('');

  const canManageLoans = canManageLoansFor(user);
  const isAdmin = isAdminUser(user);

  const authHeaders = useMemo(() => ({
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  }), [token]);

  async function api(path, options = {}) {
    const { skipAuth = false, headers: optionHeaders = {}, ...fetchOptions } = options;
    const requestHeaders = skipAuth
      ? { 'Content-Type': 'application/json', ...optionHeaders }
      : { ...authHeaders, ...optionHeaders };
    const response = await fetch(`${API_URL}${path}`, { ...fetchOptions, headers: requestHeaders });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(data.detail || Object.values(data).flat().join(' ') || 'Request failed.');
    }
    return data;
  }

  function flash(text, type = 'success') {
    setMessage(text);
    setMessageType(type);
  }

  function clearProtectedData() {
    setUser(null);
    setAccount(null);
    setTransactions([]);
    setSummary([]);
    setReceiverAccounts([]);
    setBeneficiaries([]);
    setLoans([]);
    setPendingLoans([]);
    setOverdueInstallments([]);
    setNotifications([]);
    setPendingRegistrations([]);
    setPending([]);
    setAccounts([]);
  }

  function logout() {
    localStorage.removeItem('fintrack_token');
    setToken('');
    clearProtectedData();
  }

  async function load() {
    if (!token) return;

    const [me, tx, monthly, receivers, savedBeneficiaries, loanData, notificationData] = await Promise.all([
      api('/me/'),
      api('/transactions/'),
      api('/summary/monthly/'),
      api('/accounts/'),
      api('/beneficiaries/'),
      api('/loans/'),
      api('/notifications/'),
    ]);

    setUser(me.user);
    setAccount(me.account);
    setTransactions(tx);
    setSummary(monthly);
    setReceiverAccounts(receivers);
    setBeneficiaries(savedBeneficiaries);
    setLoans(loanData);
    setNotifications(notificationData);

    const loadedIsAdmin = isAdminUser(me.user);
    const loadedCanManageLoans = canManageLoansFor(me.user);

    if (loadedIsAdmin) {
      const [pendingTx, allAccounts, overdue, loanApprovals, registrationApprovals] = await Promise.all([
        api('/admin/transactions/pending/'),
        api('/admin/accounts/'),
        api('/loans/installments/overdue/'),
        api('/loans/pending/'),
        api('/admin/registrations/pending/'),
      ]);
      setPending(pendingTx);
      setAccounts(allAccounts);
      setOverdueInstallments(overdue);
      setPendingLoans(loanApprovals);
      setPendingRegistrations(registrationApprovals);
      return;
    }

    if (loadedCanManageLoans) {
      const overdue = await api('/loans/installments/overdue/');
      setOverdueInstallments(overdue);
    } else {
      setOverdueInstallments([]);
    }

    setPending([]);
    setAccounts([]);
    setPendingLoans([]);
    setPendingRegistrations([]);
  }

  useEffect(() => {
    fetch(`${API_URL}/health/`)
      .then(async (response) => {
        const data = await response.json().catch(() => ({}));
        if (data.large_transaction_limit) setApprovalLimit(Number(data.large_transaction_limit));
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    load().catch((error) => {
      if (['User not found.', 'Invalid or expired token.'].includes(error.message)) {
        logout();
        flash('Session expired. Please sign in again.', 'error');
        return;
      }
      flash(error.message, 'error');
    });
  }, [token]);

  async function submitAuth(values) {
    setAuthBusy(true);
    try {
      let data = null;
      let lastError = null;
      const rolesToTry = [authRole, ...ROLE_OPTIONS.map((option) => option.value).filter((role) => role !== authRole)];

      for (const role of rolesToTry) {
        try {
          data = await api('/auth/login/', {
            method: 'POST',
            body: JSON.stringify({ ...values, role }),
            skipAuth: true,
          });
          break;
        } catch (error) {
          lastError = error;
          if (!error.message.includes('not registered for')) {
            throw error;
          }
        }
      }

      if (!data) throw lastError || new Error('Login failed.');
      localStorage.setItem('fintrack_token', data.token);
      setToken(data.token);
      setUser(data.user);
      setAuthRole(data.user.role);
      setMessage('');
    } catch (error) {
      flash(error.message, 'error');
    } finally {
      setAuthBusy(false);
    }
  }

  function useDemoAccount(accountInfo) {
    setAuthRole(accountInfo.role);
    loginForm.setFieldsValue({
      username: accountInfo.username,
      password: accountInfo.password,
    });
  }

  async function movement(path, values, reset) {
    try {
      const tx = await api(path, { method: 'POST', body: JSON.stringify(values) });
      const reason = tx.failure_reason ? ` ${tx.failure_reason}` : '';
      flash(`${tx.transaction_type} is ${tx.status.toLowerCase()}.${reason}`, tx.status === 'FAILED' ? 'error' : 'success');
      reset?.();
      await load();
    } catch (error) {
      flash(error.message, 'error');
    }
  }

  async function adminAction(path) {
    try {
      await api(path, { method: 'POST', body: JSON.stringify({}) });
      flash('Admin action completed.');
      await load();
    } catch (error) {
      flash(error.message, 'error');
    }
  }

  async function updateProfile(accountId, values) {
    try {
      const payload = Object.fromEntries(Object.entries(values).filter(([, value]) => value !== undefined));
      await api(`/admin/accounts/${accountId}/profile/`, {
        method: 'PATCH',
        body: JSON.stringify(payload),
      });
      flash('Profile updated.');
      await load();
    } catch (error) {
      flash(error.message, 'error');
    }
  }

  async function addBeneficiary(values, reset) {
    try {
      const beneficiary = await api('/beneficiaries/', { method: 'POST', body: JSON.stringify(values) });
      flash(`${beneficiary.username} added as beneficiary.`);
      reset?.();
      await load();
    } catch (error) {
      flash(error.message, 'error');
    }
  }

  async function issueLoan(values, reset) {
    try {
      const loan = await api('/loans/issue/', { method: 'POST', body: JSON.stringify(values) });
      flash(loan.status === 'PENDING' ? `Loan #${loan.id} sent for admin approval.` : `Loan #${loan.id} issued to ${loan.customer_username}.`);
      reset?.();
      await load();
    } catch (error) {
      flash(error.message, 'error');
    }
  }

  async function payInstallment(installmentId) {
    try {
      const installment = await api(`/loans/installments/${installmentId}/pay/`, { method: 'POST', body: JSON.stringify({}) });
      flash(`Loan installment ${installment.sequence} paid.`);
      await load();
    } catch (error) {
      flash(error.message, 'error');
    }
  }

  async function loanApprovalAction(loanId, action) {
    try {
      const loan = await api(`/loans/${loanId}/${action}/`, { method: 'POST', body: JSON.stringify({}) });
      flash(`Loan #${loan.id} ${loan.status.toLowerCase()}.`);
      await load();
    } catch (error) {
      flash(error.message, 'error');
    }
  }

  async function registerUser(values, reset) {
    try {
      const result = await api('/auth/register/', { method: 'POST', body: JSON.stringify(values) });
      const statusText = result.profile?.status === 'PENDING' ? 'sent for admin approval' : 'created and activated';
      flash(`${result.user.username} ${statusText}.`);
      reset?.();
      await load();
    } catch (error) {
      flash(error.message, 'error');
    }
  }

  async function registrationAction(profileId, action) {
    try {
      const profile = await api(`/admin/registrations/${profileId}/${action}/`, { method: 'POST', body: JSON.stringify({}) });
      flash(`${profile.user.username} registration ${profile.status.toLowerCase()}.`);
      await load();
    } catch (error) {
      flash(error.message, 'error');
    }
  }

  const transactionColumns = [
    { title: 'Type', dataIndex: 'transaction_type' },
    { title: 'Amount', dataIndex: 'amount', render: money },
    { title: 'Status', dataIndex: 'status', render: (value) => <Tag color={statusColor(value)}>{value}</Tag> },
    { title: 'From', dataIndex: 'sender_account', render: (value) => value || '-' },
    { title: 'To', dataIndex: 'receiver_account', render: (value) => value || '-' },
    { title: 'Created by', dataIndex: 'created_by_username', render: (value) => value || '-' },
    { title: 'Date', dataIndex: 'created_at', render: (value) => new Date(value).toLocaleString() },
  ];

  const filteredBeneficiaries = beneficiaries.filter((item) => matchesSearch(item, beneficiarySearch, [
    'nickname',
    'username',
    'account_number',
  ]));
  const filteredLoans = loans.filter((loan) => matchesSearch(loan, loanSearch, loanSearchFields));
  const filteredPendingLoans = pendingLoans.filter((loan) => matchesSearch(loan, loanApprovalSearch, loanSearchFields));
  const filteredOverdueInstallments = overdueInstallments.filter((item) => matchesSearch(item, overdueSearch, [
    'customer_username',
    'loan',
    'sequence',
    'due_date',
    'amount_due',
    'status',
  ]));
  const filteredNotifications = notifications.filter((item) => matchesSearch(item, notificationSearch, [
    'title',
    'message',
    'created_at',
  ]));
  const filteredTransactions = transactions.filter((tx) => matchesSearch(tx, transactionSearch, transactionSearchFields));
  const filteredPending = pending.filter((tx) => matchesSearch(tx, adminApprovalSearch, transactionSearchFields));
  const filteredAccounts = accounts.filter((item) => matchesSearch(item, accountSearch, [
    'account_number',
    'balance',
    'status',
    (accountItem) => accountItem.user,
    (accountItem) => accountItem.user?.full_name,
    (accountItem) => accountItem.user?.email,
    (accountItem) => accountItem.user?.location,
    (accountItem) => accountItem.user?.phone_number,
  ]));
  const ownPendingTransactions = transactions.filter((tx) => tx.status === 'PENDING');
  const ownPendingEmployeeDeposits = ownPendingTransactions.filter((tx) => (
    tx.transaction_type === 'DEPOSIT' && tx.created_by_username === user?.username
  ));
  const adminPendingEmployeeDeposits = pending.filter((tx) => (
    tx.transaction_type === 'DEPOSIT' && tx.created_by_role === 'EMPLOYEE'
  ));

  return (
    <ConfigProvider theme={themeConfig}>
      {!token || !user ? (
        <AuthPage
          form={loginForm}
          authBusy={authBusy}
          authRole={authRole}
          message={message}
          messageType={messageType}
          onAuthRoleChange={setAuthRole}
          onDemoAccount={useDemoAccount}
          onSubmit={submitAuth}
        />
      ) : (
        <AppShell
          user={user}
          account={account}
          canManageLoans={canManageLoans}
          isAdmin={isAdmin}
          onLogout={logout}
        >
          {message && (
            <Alert
              className="page-alert"
              type={messageType}
              message={message}
              showIcon
              closable
              onClose={() => setMessage('')}
            />
          )}

          <DashboardSection
            account={account}
            transactions={transactions}
            pending={pending}
            loans={loans}
            user={user}
            isAdmin={isAdmin}
            ownPendingTransactions={ownPendingTransactions}
            ownPendingEmployeeDeposits={ownPendingEmployeeDeposits}
            adminPendingEmployeeDeposits={adminPendingEmployeeDeposits}
          />
          <MonthlySummaryCard summary={summary} />
          <MoneySection
            user={user}
            beneficiaries={beneficiaries}
            receiverAccounts={receiverAccounts}
            onMovement={movement}
          />
          <BeneficiariesSection
            receiverAccounts={receiverAccounts}
            filteredBeneficiaries={filteredBeneficiaries}
            beneficiarySearch={beneficiarySearch}
            onBeneficiarySearch={setBeneficiarySearch}
            onAddBeneficiary={addBeneficiary}
          />

          {canManageLoans && (
            <UserRegistrationSection
              user={user}
              isAdmin={isAdmin}
              pendingRegistrations={pendingRegistrations}
              onRegisterUser={registerUser}
              onRegistrationAction={registrationAction}
            />
          )}

          <LoansSection
            user={user}
            canManageLoans={canManageLoans}
            isAdmin={isAdmin}
            receiverAccounts={receiverAccounts}
            filteredLoans={filteredLoans}
            filteredPendingLoans={filteredPendingLoans}
            filteredOverdueInstallments={filteredOverdueInstallments}
            loanSearch={loanSearch}
            loanApprovalSearch={loanApprovalSearch}
            overdueSearch={overdueSearch}
            onLoanSearch={setLoanSearch}
            onLoanApprovalSearch={setLoanApprovalSearch}
            onOverdueSearch={setOverdueSearch}
            onIssueLoan={issueLoan}
            onPayInstallment={payInstallment}
            onLoanApprovalAction={loanApprovalAction}
          />
          <NotificationsSection
            filteredNotifications={filteredNotifications}
            notificationSearch={notificationSearch}
            onNotificationSearch={setNotificationSearch}
          />
          <TransactionHistorySection
            columns={transactionColumns}
            filteredTransactions={filteredTransactions}
            transactionSearch={transactionSearch}
            onTransactionSearch={setTransactionSearch}
          />

          {isAdmin && (
            <AdminApprovalsSection
              columns={transactionColumns}
              filteredPending={filteredPending}
              filteredAccounts={filteredAccounts}
              adminApprovalSearch={adminApprovalSearch}
              accountSearch={accountSearch}
              onAdminApprovalSearch={setAdminApprovalSearch}
              onAccountSearch={setAccountSearch}
              onAdminAction={adminAction}
              onProfileUpdate={updateProfile}
            />
          )}
        </AppShell>
      )}
    </ConfigProvider>
  );
}
