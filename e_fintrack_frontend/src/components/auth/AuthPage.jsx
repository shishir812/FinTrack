import { Alert, Avatar, Button, Card, Form, Input, Segmented, Space, Typography } from 'antd';
import { BankOutlined, LoginOutlined } from '@ant-design/icons';
import { DEMO_ACCOUNTS, ROLE_HELP, ROLE_OPTIONS } from '../../config';

const { Title, Text } = Typography;

export default function AuthPage({
  form,
  authBusy,
  authRole,
  message,
  messageType,
  onAuthRoleChange,
  onDemoAccount,
  onSubmit,
}) {
  const selectedDemoAccount = DEMO_ACCOUNTS.find((accountInfo) => accountInfo.role === authRole);

  return (
    <main className="auth-shell ant-auth">
      <Card className="auth-card" variant="borderless">
        <Space align="center" size={14} className="auth-brand">
          <Avatar size={48} icon={<BankOutlined />} className="brand-avatar" />
          <div>
            <Title level={2}>FinTrack</Title>
            <Text type="secondary">Secure banking dashboard</Text>
          </div>
        </Space>

        <div className="role-picker">
          <Text strong>Login as</Text>
          <Segmented block options={ROLE_OPTIONS} value={authRole} onChange={onAuthRoleChange} />
          <Text type="secondary">{ROLE_HELP[authRole]}</Text>
        </div>

        <div className="demo-credentials">
          <Text strong>Demo access</Text>
          <div className="demo-account-list">
            {selectedDemoAccount && (
              <Button
                key={selectedDemoAccount.role}
                className="demo-account-button"
                onClick={() => onDemoAccount(selectedDemoAccount)}
              >
                <span>{selectedDemoAccount.label}</span>
                <Text code>{selectedDemoAccount.username} / {selectedDemoAccount.password}</Text>
              </Button>
            )}
          </div>
        </div>

        <Form form={form} layout="vertical" onFinish={onSubmit} requiredMark={false}>
          <Form.Item name="username" rules={[{ required: true, message: 'Username is required' }]}>
            <Input size="large" placeholder="Username" />
          </Form.Item>
          <Form.Item name="password" rules={[{ required: true, message: 'Password is required' }]}>
            <Input.Password size="large" placeholder="Password" />
          </Form.Item>
          <Button block size="large" type="primary" htmlType="submit" loading={authBusy} icon={<LoginOutlined />}>
            Sign in
          </Button>
        </Form>

        {message && <Alert className="top-alert" type={messageType} message={message} showIcon />}
      </Card>
    </main>
  );
}
