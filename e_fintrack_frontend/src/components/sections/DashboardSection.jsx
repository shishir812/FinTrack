import { Card, Col, Row, Statistic, Typography } from 'antd';
import { CheckCircleOutlined, CreditCardOutlined, WalletOutlined } from '@ant-design/icons';
import { money } from '../../utils/formatters';

const { Text } = Typography;

export default function DashboardSection({
  account,
  transactions,
  pending,
  loans,
  user,
  isAdmin,
  ownPendingTransactions,
  ownPendingEmployeeDeposits,
  adminPendingEmployeeDeposits,
}) {
  return (
    <section id="dashboard">
      <Row gutter={[16, 16]} className="dashboard-row">
        <Col xs={24} md={12} xl={6}>
          <Card className="balance-card">
            <Statistic title="Available balance" value={Number(account?.balance || 0)} precision={2} prefix="BDT" />
            <Text>{account?.account_number}</Text>
          </Card>
        </Col>
        <Col xs={24} md={12} xl={6}>
          <Card>
            <Statistic title="Total transactions" value={transactions.length} prefix={<WalletOutlined />} />
            <Text type="secondary">Pending, success, and failed</Text>
          </Card>
        </Col>
        <Col xs={24} md={12} xl={6}>
          <Card>
            <Statistic
              title={isAdmin ? 'Transaction approvals' : 'Pending approval'}
              value={isAdmin ? pending.length : ownPendingTransactions.length}
              prefix={<CheckCircleOutlined />}
            />
            <Text type="secondary">{isAdmin ? 'Deposits, transfers, and withdrawals' : 'Waiting for admin decision'}</Text>
          </Card>
        </Col>
        <Col xs={24} md={12} xl={6}>
          <Card>
            <Statistic
              title={isAdmin ? 'Employee deposits' : user.role === 'EMPLOYEE' ? 'My deposit approvals' : 'Active loans'}
              value={
                isAdmin
                  ? adminPendingEmployeeDeposits.length
                  : user.role === 'EMPLOYEE'
                    ? ownPendingEmployeeDeposits.length
                    : loans.filter((loan) => loan.status === 'ACTIVE').length
              }
              prefix={<CreditCardOutlined />}
            />
            <Text type="secondary">{isAdmin ? 'Waiting to settle into bank balance' : user.role === 'EMPLOYEE' ? 'Submitted to admin' : 'Repayment plans'}</Text>
          </Card>
        </Col>
      </Row>
    </section>
  );
}
