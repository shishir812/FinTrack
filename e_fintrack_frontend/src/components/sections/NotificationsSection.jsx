import { Badge, Card, Empty, List, Space } from 'antd';
import { BellOutlined } from '@ant-design/icons';
import SearchBox from '../shared/SearchBox';

export default function NotificationsSection({ filteredNotifications, notificationSearch, onNotificationSearch }) {
  return (
    <Card
      id="notifications"
      title={<Space><BellOutlined /> Notifications</Space>}
      className="section-card"
      extra={<SearchBox value={notificationSearch} onChange={onNotificationSearch} placeholder="Search notifications" />}
    >
      <List
        dataSource={filteredNotifications}
        locale={{ emptyText: <Empty description="No notifications yet" /> }}
        renderItem={(item) => (
          <List.Item>
            <List.Item.Meta title={item.title} description={item.message} />
            {!item.is_read && <Badge status="processing" />}
          </List.Item>
        )}
      />
    </Card>
  );
}
