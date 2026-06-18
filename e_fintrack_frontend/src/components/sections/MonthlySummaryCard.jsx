import { Card } from 'antd';

export default function MonthlySummaryCard({ summary }) {
  return (
    <Card title="Monthly income and expense" className="section-card">
      <div className="chart">
        {(summary.length ? summary : [{ month: 'No data', income: 0, expense: 0 }]).map((item) => {
          const max = Math.max(Number(item.income), Number(item.expense), 1);
          return (
            <div className="bar-group" key={item.month}>
              <div className="bars">
                <span className="income" style={{ height: `${(Number(item.income) / max) * 100}%` }} />
                <span className="expense" style={{ height: `${(Number(item.expense) / max) * 100}%` }} />
              </div>
              <small>{item.month}</small>
            </div>
          );
        })}
      </div>
    </Card>
  );
}
