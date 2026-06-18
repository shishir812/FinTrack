import { Alert, Button, Card, Form, Input, Select } from 'antd';
import { UserAddOutlined } from '@ant-design/icons';
import { isAdminUser } from '../../utils/roles';

export default function UserRegistrationForm({ user, onFinish }) {
  const [form] = Form.useForm();
  const isAdmin = isAdminUser(user);
  const options = isAdmin
    ? [
        { label: 'Member', value: 'CUSTOMER' },
        { label: 'Bank employee', value: 'EMPLOYEE' },
      ]
    : [{ label: 'Member', value: 'CUSTOMER' }];

  return (
    <Card title={isAdmin ? 'Register user' : 'Request member registration'}>
      {!isAdmin && (
        <Alert
          className="form-alert"
          type="warning"
          showIcon
          message="Employee-created members require admin approval before login."
        />
      )}
      <Form
        form={form}
        layout="vertical"
        initialValues={{ role: 'CUSTOMER' }}
        onFinish={(values) => onFinish(values, () => form.resetFields())}
      >
        <Form.Item name="role" rules={[{ required: true, message: 'Role is required' }]}>
          <Select options={options} />
        </Form.Item>
        <Form.Item name="username" rules={[{ required: true, message: 'Username is required' }]}>
          <Input placeholder="Username" />
        </Form.Item>
        <Form.Item name="email">
          <Input placeholder="Email" />
        </Form.Item>
        <Form.Item name="first_name">
          <Input placeholder="First name" />
        </Form.Item>
        <Form.Item name="last_name">
          <Input placeholder="Last name" />
        </Form.Item>
        <Form.Item name="location">
          <Input placeholder="Location" />
        </Form.Item>
        <Form.Item name="phone_number">
          <Input placeholder="Phone number" />
        </Form.Item>
        <Form.Item
          name="password"
          rules={[
            { required: true, message: 'Password is required' },
            { min: 6, message: 'Use at least 6 characters' },
          ]}
        >
          <Input.Password placeholder="Temporary password" />
        </Form.Item>
        <Button type="primary" htmlType="submit" block icon={<UserAddOutlined />}>
          {isAdmin ? 'Create user' : 'Submit for approval'}
        </Button>
      </Form>
    </Card>
  );
}
