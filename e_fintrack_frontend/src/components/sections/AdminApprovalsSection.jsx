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
            title="Account holders"
            extra={<SearchBox value={accountSearch} onChange={onAccountSearch} placeholder="Search account holder" />}
          >
            <List
              className="account-status-list"
              dataSource={filteredAccounts}
              renderItem={(item) => (
                <List.Item className="account-status-item">
                  <div className="account-status-content">
                    <div className="account-status-header">
                      <div className="account-holder-identity">
                        <span className="account-holder-label">Account holder</span>
                        <strong>{item.user.full_name || item.user.username}</strong>
                      </div>
                      <Tag color={statusColor(item.status)}>{item.status}</Tag>
                    </div>

                    <div className="account-details">
                      <div className="account-detail">
                        <span>Username</span>
                        <strong>{item.user.username}</strong>
                      </div>
                      <div className="account-detail">
                        <span>Account number</span>
                        <strong>{item.account_number}</strong>
                      </div>
                      <div className="account-detail">
                        <span>Available balance</span>
                        <strong>{money(item.balance)}</strong>
                      </div>
                      {item.user.email && (
                        <div className="account-detail">
                          <span>Email</span>
                          <strong>{item.user.email}</strong>
                        </div>
                      )}
                      {item.user.location && (
                        <div className="account-detail">
                          <span>Location</span>
                          <strong>{item.user.location}</strong>
                        </div>
                      )}
                      {item.user.phone_number && (
                        <div className="account-detail">
                          <span>Phone number</span>
                          <strong>{item.user.phone_number}</strong>
                        </div>
                      )}
                    </div>

                    <div className="account-status-actions">
                      <Button onClick={() => openProfileEditor(item)}>Edit profile</Button>
                      <Button onClick={() => onAdminAction(`/admin/accounts/${item.id}/${item.status === 'ACTIVE' ? 'freeze' : 'unfreeze'}/`)}>
                        {item.status === 'ACTIVE' ? 'Freeze account' : 'Unfreeze account'}
                      </Button>
                    </div>
                  </div>
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
