import { Card, Col, Empty, List, Row, Tag } from 'antd';
import BeneficiaryForm from '../forms/BeneficiaryForm';
import SearchBox from '../shared/SearchBox';

export default function BeneficiariesSection({
  receiverAccounts,
  filteredBeneficiaries,
  beneficiarySearch,
  onBeneficiarySearch,
  onAddBeneficiary,
}) {
  return (
    <section id="beneficiaries">
      <Row gutter={[16, 16]} className="section-row">
        <Col xs={24} lg={8}>
          <BeneficiaryForm receiverAccounts={receiverAccounts} onFinish={onAddBeneficiary} />
        </Col>
        <Col xs={24} lg={16}>
          <Card
            title="Saved beneficiaries"
            extra={<SearchBox value={beneficiarySearch} onChange={onBeneficiarySearch} placeholder="Search beneficiary" />}
          >
            <List
              dataSource={filteredBeneficiaries}
              locale={{ emptyText: <Empty description="No beneficiaries saved yet" /> }}
              renderItem={(item) => (
                <List.Item>
                  <List.Item.Meta title={item.nickname || item.username} description={`${item.username} - ${item.account_number}`} />
                  <Tag color="cyan">{item.account_number}</Tag>
                </List.Item>
              )}
            />
          </Card>
        </Col>
      </Row>
    </section>
  );
}
