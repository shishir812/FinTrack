import { Alert, Button, Card, Form, Input, InputNumber, Select } from 'antd';

export default function LoanIssueForm({ user, receiverAccounts, onFinish }) {
  const [form] = Form.useForm();
  const options = receiverAccounts
    .filter((item) => item.user.role === 'CUSTOMER')
    .map((item) => ({
      label: `${item.user.username} - ${item.account_number}`,
      value: item.account_number,
    }));

  return (
    <Card title="Issue loan">
      {user.role === 'EMPLOYEE' && (
        <Alert
          className="form-alert"
          type="warning"
          showIcon
          message="Employee loan requests require admin approval before money is disbursed."
        />
      )}
      <Form
        form={form}
        layout="vertical"
        initialValues={{ annual_interest_rate: 12, term_months: 12 }}
        onFinish={(values) => onFinish(values, () => form.resetFields())}
      >
        <Form.Item name="customer" rules={[{ required: true, message: 'Customer is required' }]}>
          <Select showSearch placeholder="Customer username or account" options={options} />
        </Form.Item>
        <Form.Item name="principal" rules={[{ required: true, message: 'Principal is required' }]}>
          <InputNumber min={1} placeholder="Principal" style={{ width: '100%' }} />
        </Form.Item>
        <Form.Item name="annual_interest_rate" rules={[{ required: true, message: 'Interest is required' }]}>
          <InputNumber min={0} placeholder="Annual interest %" style={{ width: '100%' }} />
        </Form.Item>
        <Form.Item name="term_months" rules={[{ required: true, message: 'Term is required' }]}>
          <InputNumber min={1} placeholder="Term months" style={{ width: '100%' }} />
        </Form.Item>
        <Form.Item name="purpose">
          <Input placeholder="Purpose" />
        </Form.Item>
        <Button type="primary" htmlType="submit" block>
          Issue loan
        </Button>
      </Form>
    </Card>
  );
}
