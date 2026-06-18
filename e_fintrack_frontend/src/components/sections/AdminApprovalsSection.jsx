import { useState } from 'react';
import { Button, Card, Col, Form, Input, List, Modal, Row, Space, Table, Tag } from 'antd';
import SearchBox from '../shared/SearchBox';
import { money, statusColor } from '../../utils/formatters';

export default function AdminApprovalsSection({
  columns,
  filteredPending,
  filteredAccounts,
  adminApprovalSearch,
  accountSearch,
  onAdminApprovalSearch,
  onAccountSearch,
  onAdminAction,
  onProfileUpdate,
}) {
  const [form] = Form.useForm();
  const [editingAccount, setEditingAccount] = useState(null);

  function openProfileEditor(account) {
    setEditingAccount(account);
    form.setFieldsValue({
      first_name: account.user.first_name,
      last_name: account.user.last_name,
      email: account.user.email,
      location: account.user.location,
      phone_number: account.user.phone_number,
      password: '',
    });
  }

  async function submitProfileUpdate() {
    const values = await form.validateFields();
    await onProfileUpdate(editingAccount.id, values);
    setEditingAccount(null);
    form.resetFields();
  }

  return (
    <section id="admin">
      <Row gutter={[16, 16]} className="section-row admin-row">
        <Col xs={24} xl={14}>
          <Card
            title="Admin approvals"
            extra={<SearchBox value={adminApprovalSearch} onChange={onAdminApprovalSearch} placeholder="Search approval" />}
          >
            <Table
              rowKey="id"
              dataSource={filteredPending}
              scroll={{ x: true }}
              columns={[
                ...columns,
                {
                  title: 'Action',
                  render: (_, tx) => (
                    <Space>
                      <Button onClick={() => onAdminAction(`/admin/transactions/${tx.id}/approve/`)}>Approve</Button>
                      <Button danger onClick={() => onAdminAction(`/admin/transactions/${tx.id}/reject/`)}>Reject</Button>
                    </Space>
                  ),
                },
              ]}
            />
          </Card>
        </Col>
        <Col xs={24} xl={10}>
          <Card
            title="Account status"
            extra={<SearchBox value={accountSearch} onChange={onAccountSearch} placeholder="Search employee or member" />}
          >
            <List
              dataSource={filteredAccounts}
              renderItem={(item) => (
                <List.Item
                  actions={[
                    <Button key="edit" onClick={() => openProfileEditor(item)}>
                      Edit profile
                    </Button>,
                    <Button key="status" onClick={() => onAdminAction(`/admin/accounts/${item.id}/${item.status === 'ACTIVE' ? 'freeze' : 'unfreeze'}/`)}>
                      {item.status === 'ACTIVE' ? 'Freeze' : 'Unfreeze'}
                    </Button>,
                  ]}
                >
                  <List.Item.Meta
                    title={item.user.full_name || item.user.username}
                    description={`${item.user.username} - ${item.account_number} - ${money(item.balance)}${item.user.location ? ` - ${item.user.location}` : ''}${item.user.phone_number ? ` - ${item.user.phone_number}` : ''}`}
                  />
                  <Tag color={statusColor(item.status)}>{item.status}</Tag>
                </List.Item>
              )}
            />
          </Card>
        </Col>
      </Row>

      <Modal
        title={editingAccount ? `Edit ${editingAccount.user.username}` : 'Edit profile'}
        open={Boolean(editingAccount)}
        okText="Save profile"
        onOk={submitProfileUpdate}
        onCancel={() => {
          setEditingAccount(null);
          form.resetFields();
        }}
      >
        <Form form={form} layout="vertical">
          <Form.Item name="first_name" label="First name">
            <Input placeholder="First name" />
          </Form.Item>
          <Form.Item name="last_name" label="Last name">
            <Input placeholder="Last name" />
          </Form.Item>
          <Form.Item name="email" label="Email">
            <Input placeholder="Email" />
          </Form.Item>
          <Form.Item name="location" label="Location">
            <Input placeholder="Location" />
          </Form.Item>
          <Form.Item name="phone_number" label="Phone number">
            <Input placeholder="Phone number" />
          </Form.Item>
          <Form.Item name="password" label="New password" rules={[{ min: 6, message: 'Use at least 6 characters' }]}>
            <Input.Password placeholder="Leave blank to keep current password" />
          </Form.Item>
        </Form>
      </Modal>
    </section>
  );
}
