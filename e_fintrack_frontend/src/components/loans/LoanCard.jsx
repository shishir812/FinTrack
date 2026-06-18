import { Alert, Button, Card, Descriptions, List, Space, Tag } from 'antd';
import { money, statusColor } from '../../utils/formatters';
import { isAdminUser } from '../../utils/roles';

export default function LoanCard({ loan, user, canManageLoans, payInstallment, loanApprovalAction }) {
  const payableInstallments = loan.installments.filter((item) => item.status === 'PENDING' || item.status === 'OVERDUE');
  const isAdmin = isAdminUser(user);

  return (
    <List.Item className="loan-list-item">
      <Card className="loan-card" size="small">
        <Space className="loan-card-head" align="start">
          <Descriptions title={`Loan #${loan.id}`} size="small" column={{ xs: 1, md: 2, xl: 4 }}>
            <Descriptions.Item label="Customer">{loan.customer_username}</Descriptions.Item>
            <Descriptions.Item label="Principal">{money(loan.principal)}</Descriptions.Item>
            <Descriptions.Item label="Monthly">{money(loan.monthly_payment)}</Descriptions.Item>
            <Descriptions.Item label="Remaining">{money(loan.remaining_amount)}</Descriptions.Item>
          </Descriptions>
          <Tag color={statusColor(loan.status)}>{loan.status}</Tag>
        </Space>

        {loan.status === 'PENDING' && (
          <Alert
            className="loan-alert"
            type="warning"
            showIcon
            message="Waiting for admin approval. Money is not disbursed yet."
            action={isAdmin && (
              <Space>
                <Button size="small" onClick={() => loanApprovalAction(loan.id, 'approve')}>Approve</Button>
                <Button size="small" danger onClick={() => loanApprovalAction(loan.id, 'reject')}>Reject</Button>
              </Space>
            )}
          />
        )}

        {loan.status === 'REJECTED' && loan.rejection_reason && (
          <Alert className="loan-alert" type="error" message={loan.rejection_reason} />
        )}

        {!!loan.installments.length && (
          <List
            size="small"
            dataSource={loan.installments.slice(0, canManageLoans ? 3 : 6)}
            renderItem={(item) => (
              <List.Item
                actions={!canManageLoans && (item.status === 'PENDING' || item.status === 'OVERDUE') && item.id === payableInstallments[0]?.id ? [
                  <Button key="pay" type="primary" size="small" onClick={() => payInstallment(item.id)}>Pay</Button>,
                ] : []}
              >
                <List.Item.Meta title={`Installment #${item.sequence}`} description={`Due ${item.due_date} - ${money(item.amount_due)}`} />
                <Tag color={statusColor(item.status)}>{item.status}</Tag>
              </List.Item>
            )}
          />
        )}
      </Card>
    </List.Item>
  );
}
