import { Alert, Button, Card, Form, Input, InputNumber } from 'antd';
import { WalletOutlined } from '@ant-design/icons';

export default function MoneyForm({ title, note, onFinish }) {
  const [form] = Form.useForm();

  return (
    <Card title={title}>
      {note && <Alert className="form-alert" type="info" showIcon message={note} />}
      <Form form={form} layout="vertical" onFinish={(values) => onFinish(values, form)}>
        <Form.Item name="amount" rules={[{ required: true, message: 'Amount is required' }]}>
          <InputNumber min={1} placeholder="Amount" style={{ width: '100%' }} />
        </Form.Item>
        <Form.Item name="description">
          <Input placeholder="Description" />
        </Form.Item>
        <Button type="primary" htmlType="submit" block icon={<WalletOutlined />}>
          {title}
        </Button>
      </Form>
    </Card>
  );
}
