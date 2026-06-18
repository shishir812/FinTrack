import { useState } from 'react';
import { Avatar, Button, Drawer, Layout, Menu, Space, Tag, Typography } from 'antd';
import {
  AuditOutlined,
  BankOutlined,
  BellOutlined,
  CreditCardOutlined,
  DashboardOutlined,
  LogoutOutlined,
  MenuOutlined,
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
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const menuItems = buildMenuItems({ canManageLoans, isAdmin });
  const renderMenu = () => (
    <Menu mode="inline" items={menuItems} className="side-menu" onClick={() => setMobileMenuOpen(false)} />
  );

  return (
    <Layout className="app-layout">
      <Sider width={272} className="app-sider">
        <Space align="center" size={12} className="sider-brand">
          <Avatar icon={<BankOutlined />} className="brand-avatar" />
          <div>
            <Title level={4}>FinTrack</Title>
            <Text>{user.username}</Text>
          </div>
        </Space>
        {renderMenu()}
        <Button icon={<LogoutOutlined />} onClick={onLogout} block className="logout-button">
          Logout
        </Button>
      </Sider>

      <Layout>
        <Header className="app-header">
          <div className="header-title">
            <Button
              type="text"
              icon={<MenuOutlined />}
              className="mobile-menu-button"
              onClick={() => setMobileMenuOpen(true)}
              aria-label="Open navigation"
            />
            <div>
              <Title level={3}>{user.username}</Title>
              <Text type="secondary">FinTrack dashboard</Text>
            </div>
          </div>
          <Space wrap>
            <Tag color="blue">{user.role}</Tag>
            <Tag color={statusColor(account?.status)}>{account?.status}</Tag>
          </Space>
        </Header>
        <Content className="app-content">{children}</Content>
      </Layout>

      <Drawer
        title={(
          <Space align="center" size={12}>
            <Avatar icon={<BankOutlined />} className="brand-avatar" />
            <span>FinTrack</span>
          </Space>
        )}
        placement="left"
        open={mobileMenuOpen}
        onClose={() => setMobileMenuOpen(false)}
        width={300}
        className="mobile-nav-drawer"
      >
        {renderMenu()}
        <Button icon={<LogoutOutlined />} onClick={onLogout} block className="logout-button">
          Logout
        </Button>
      </Drawer>
    </Layout>
  );
}
