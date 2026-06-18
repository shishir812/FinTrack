import { Card, Col, Empty, List, Row, Tag } from 'antd';
import LoanIssueForm from '../forms/LoanIssueForm';
import LoanCard from '../loans/LoanCard';
import SearchBox from '../shared/SearchBox';
import { money } from '../../utils/formatters';

export default function LoansSection({
  user,
  canManageLoans,
  isAdmin,
  receiverAccounts,
  filteredLoans,
  filteredPendingLoans,
  filteredOverdueInstallments,
  loanSearch,
  loanApprovalSearch,
  overdueSearch,
  onLoanSearch,
  onLoanApprovalSearch,
  onOverdueSearch,
  onIssueLoan,
  onPayInstallment,
  onLoanApprovalAction,
}) {
  return (
    <>
      <section id="loans" className="section-row">
        <Row gutter={[16, 16]}>
          {canManageLoans && (
            <Col xs={24} lg={8}>
              <LoanIssueForm user={user} receiverAccounts={receiverAccounts} onFinish={onIssueLoan} />
            </Col>
          )}
          <Col xs={24} lg={canManageLoans ? 16 : 24}>
            <Card
              title={canManageLoans ? 'Loan portfolio' : 'My loans'}
              extra={<SearchBox value={loanSearch} onChange={onLoanSearch} placeholder="Search loan or customer" />}
            >
              <List
                dataSource={filteredLoans}
                locale={{ emptyText: <Empty description="No loans yet" /> }}
                renderItem={(loan) => (
                  <LoanCard
                    loan={loan}
                    user={user}
                    canManageLoans={canManageLoans}
                    payInstallment={onPayInstallment}
                    loanApprovalAction={onLoanApprovalAction}
                  />
                )}
              />
            </Card>
          </Col>
        </Row>
      </section>

      {isAdmin && (
        <Card
          title="Loan issue approvals"
          className="section-card"
          extra={<SearchBox value={loanApprovalSearch} onChange={onLoanApprovalSearch} placeholder="Search loan request" />}
        >
          <List
            dataSource={filteredPendingLoans}
            locale={{ emptyText: <Empty description="No loan requests waiting for approval" /> }}
            renderItem={(loan) => (
              <LoanCard
                loan={loan}
                user={user}
                canManageLoans
                payInstallment={onPayInstallment}
                loanApprovalAction={onLoanApprovalAction}
              />
            )}
          />
        </Card>
      )}

      {canManageLoans && (
        <Card
          title="Missed loan payments"
          className="section-card"
          extra={<SearchBox value={overdueSearch} onChange={onOverdueSearch} placeholder="Search overdue loan" />}
        >
          <List
            dataSource={filteredOverdueInstallments}
            locale={{ emptyText: <Empty description="No overdue installments" /> }}
            renderItem={(item) => (
              <List.Item>
                <List.Item.Meta title={item.customer_username} description={`Loan #${item.loan} installment ${item.sequence} due ${item.due_date}`} />
                <Tag color="red">{money(item.amount_due)}</Tag>
              </List.Item>
            )}
          />
        </Card>
      )}
    </>
  );
}
