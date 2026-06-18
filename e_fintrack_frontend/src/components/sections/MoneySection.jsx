import { Col, Row } from 'antd';
import MoneyForm from '../forms/MoneyForm';
import TransferCard from '../forms/TransferCard';

export default function MoneySection({ user, beneficiaries, receiverAccounts, onMovement }) {
  return (
    <section id="move-money">
      <Row gutter={[16, 16]} className="money-row">
        <Col xs={24} xl={8}>
          <MoneyForm
            title={user.role === 'EMPLOYEE' ? 'Bank deposit' : 'Deposit'}
            note={user.role === 'EMPLOYEE' ? 'Employee deposits go to admin approval before they settle into the bank account.' : ''}
            onFinish={(values, form) => onMovement('/transactions/deposit/', values, () => form.resetFields())}
          />
        </Col>
        <Col xs={24} xl={8}>
          <MoneyForm title="Withdraw" onFinish={(values, form) => onMovement('/transactions/withdraw/', values, () => form.resetFields())} />
        </Col>
        <Col xs={24} xl={8}>
          <TransferCard
            beneficiaries={beneficiaries}
            receiverAccounts={receiverAccounts}
            onFinish={(values, form) => onMovement('/transactions/transfer/', values, () => form.resetFields())}
          />
        </Col>
      </Row>
    </section>
  );
}
