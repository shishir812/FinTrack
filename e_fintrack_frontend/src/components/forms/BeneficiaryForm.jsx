import { Button, Card, Form, Input, Select } from 'antd';

export default function BeneficiaryForm({ receiverAccounts, onFinish }) {
  const [form] = Form.useForm();
  const options = receiverAccounts.map((item) => ({
    label: `${item.user.username} - ${item.account_number}`,
    value: item.account_number,
  }));

  return (
    <Card title="Add beneficiary">
      <Form form={form} layout="vertical" onFinish={(values) => onFinish(values, () => form.resetFields())}>
        <Form.Item name="account_number" rules={[{ required: true, message: 'Beneficiary is required' }]}>
          <Select
            showSearch
            placeholder="Username or account number"
            options={options}
            optionFilterProp="label"
            filterOption={(input, option) => (option?.label || '').toLowerCase().includes(input.toLowerCase())}
          />
        </Form.Item>
        <Form.Item name="nickname">
          <Input placeholder="Nickname" />
        </Form.Item>
        <Button type="primary" htmlType="submit" block>
          Save beneficiary
        </Button>
      </Form>
    </Card>
  );
}
