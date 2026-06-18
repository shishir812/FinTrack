import { Button, Card, Col, Empty, List, Row, Tag } from 'antd';
import UserRegistrationForm from '../forms/UserRegistrationForm';
import { statusColor } from '../../utils/formatters';

export default function UserRegistrationSection({
  user,
  isAdmin,
  pendingRegistrations,
  onRegisterUser,
  onRegistrationAction,
}) {
  return (
    <section id="user-registration" className="section-row">
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={8}>
          <UserRegistrationForm user={user} onFinish={onRegisterUser} />
        </Col>
        {isAdmin && (
          <Col xs={24} lg={16}>
            <Card title="Member registration approvals">
              <List
                dataSource={pendingRegistrations}
                locale={{ emptyText: <Empty description="No member registrations waiting for approval" /> }}
                renderItem={(item) => (
                  <List.Item
                    actions={[
                      <Button key="approve" onClick={() => onRegistrationAction(item.id, 'approve')}>Approve</Button>,
                      <Button key="reject" danger onClick={() => onRegistrationAction(item.id, 'reject')}>Reject</Button>,
                    ]}
                  >
                    <List.Item.Meta
                      title={item.user.username}
                      description={`${item.user.email || 'No email'} - requested by ${item.created_by_username || 'bank staff'}`}
                    />
                    <Tag color={statusColor(item.status)}>{item.status}</Tag>
                  </List.Item>
                )}
              />
            </Card>
          </Col>
        )}
      </Row>
    </section>
  );
}
