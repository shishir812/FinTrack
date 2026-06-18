import { Card, Table } from 'antd';
import SearchBox from '../shared/SearchBox';

export default function TransactionHistorySection({
  columns,
  filteredTransactions,
  transactionSearch,
  onTransactionSearch,
}) {
  return (
    <Card
      id="history"
      title="Transaction history"
      className="section-card"
      extra={<SearchBox value={transactionSearch} onChange={onTransactionSearch} placeholder="Search transaction" />}
    >
      <Table rowKey="id" columns={columns} dataSource={filteredTransactions} scroll={{ x: true }} />
    </Card>
  );
}
