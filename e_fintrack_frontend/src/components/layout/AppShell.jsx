import { Avatar, Button, Layout, Menu, Space, Tag, Typography } from 'antd';
import {
  AuditOutlined,
  BankOutlined,
  BellOutlined,
  CreditCardOutlined,
  DashboardOutlined,
  LogoutOutlined,
  SendOutlined,
  TeamOutlined,
  UserAddOutlined,
} from '@ant-design/icons';
import { statusColor } from '../../utils/formatters';

const { Header, Sider, Content } = Layout;
const { Title, Text } = Typography;

function buildMenuItems({ canManageLoans, isAdmin }) {
  return [
    { key: 'dashboard', icon: <DashboardOutlined />, label: <a href="#dashboard">Dashboard</a> },
    { key: 'money', icon: <SendOutlined />, label: <a href="#move-money">Move money</a> },
    { key: 'beneficiaries', icon: <TeamOutlined />, label: <a href="#beneficiaries">Beneficiaries</a> },
    ...(canManageLoans ? [{ key: 'users', icon: <UserAddOutlined />, label: <a href="#user-registration">Users</a> }] : []),
    { key: 'loans', icon: <CreditCardOutlined />, label: <a href="#loans">Loans</a> },
    { key: 'notifications', icon: <BellOutlined />, label: <a href="#notifications">Notifications</a> },
    { key: 'history', icon: <AuditOutlined />, label: <a href="#history">History</a> },
    ...(isAdmin ? [{ key: 'admin', icon: <BankOutlined />, label: <a href="#admin">Approvals</a> }] : []),
  ];
}

export default function AppShell({ user, account, canManageLoans, isAdmin, onLogout, children }) {
  const menuItems = buildMenuItems({ canManageLoans, isAdmin });

  return (
    <Layout className="app-layout">
      <Sider width={272} className="app-sider" breakpoint="lg" collapsedWidth="0">
        <Space align="center" size={12} className="sider-brand">
          <Avatar icon={<BankOutlined />} className="brand-avatar" />
          <div>
            <Title level={4}>FinTrack</Title>
            <Text>{user.username}</Text>
          </div>
        </Space>
        <Menu mode="inline" items={menuItems} className="side-menu" />
        <Button icon={<LogoutOutlined />} onClick={onLogout} block className="logout-button">
          Logout
        </Button>
      </Sider>

      <Layout>
        <Header className="app-header">
          <div>
            <Title level={3}>{user.username}</Title>
          </div>
          <Space wrap>
            <Tag color="blue">{user.role}</Tag>
            <Tag color={statusColor(account?.status)}>{account?.status}</Tag>
          </Space>
        </Header>
        <Content className="app-content">{children}</Content>
      </Layout>
    </Layout>
  );
}
