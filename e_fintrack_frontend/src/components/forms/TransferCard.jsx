import { Alert, Button, Card, Form, Input, InputNumber, Select, Segmented } from 'antd';
import { SendOutlined } from '@ant-design/icons';
import { useState } from 'react';

export default function TransferCard({ beneficiaries, receiverAccounts, onFinish }) {
  const [form] = Form.useForm();
  const [transferMode, setTransferMode] = useState('BENEFICIARY');
  const beneficiaryOptions = beneficiaries.map((item) => ({
    label: `${item.nickname || item.username} - ${item.account_number}`,
    value: item.id,
  }));
  const accountOptions = receiverAccounts.map((item) => ({
    label: `${item.user.username} - ${item.account_number}`,
    value: item.account_number,
  }));

  function submitTransfer(values) {
    const payload = transferMode === 'BENEFICIARY'
      ? {
          beneficiary_id: values.beneficiary_id,
          amount: values.amount,
          description: values.description || '',
        }
      : {
          receiver_account_number: values.receiver_account_number,
          amount: values.amount,
          description: values.description || '',
        };
    onFinish(payload, form);
  }

  return (
    <Card title="Transfer">
      <Segmented
        block
        className="transfer-mode"
        value={transferMode}
        onChange={(value) => {
          setTransferMode(value);
          form.resetFields(['beneficiary_id', 'receiver_account_number']);
        }}
        options={[
          { label: 'Saved beneficiary', value: 'BENEFICIARY' },
          { label: 'Any account', value: 'ACCOUNT' },
        ]}
      />
      <Form form={form} layout="vertical" onFinish={submitTransfer}>
        {transferMode === 'BENEFICIARY' ? (
          <>
            {!beneficiaries.length && (
              <Alert
                className="form-alert"
                type="info"
                showIcon
                message="Add a beneficiary first, then select it here for transfer."
              />
            )}
            <Form.Item name="beneficiary_id" rules={[{ required: true, message: 'Beneficiary is required' }]}>
              <Select
                showSearch
                disabled={!beneficiaries.length}
                placeholder="Saved beneficiary account"
                options={beneficiaryOptions}
                optionFilterProp="label"
              />
            </Form.Item>
          </>
        ) : (
          <Form.Item name="receiver_account_number" rules={[{ required: true, message: 'Receiver is required' }]}>
            <Select
              showSearch
              placeholder="Receiver username or account"
              options={accountOptions}
              optionFilterProp="label"
            />
          </Form.Item>
        )}
        <Form.Item name="amount" rules={[{ required: true, message: 'Amount is required' }]}>
          <InputNumber min={1} placeholder="Amount" style={{ width: '100%' }} />
        </Form.Item>
        <Form.Item name="description">
          <Input placeholder="Description" />
        </Form.Item>
        <Button type="primary" htmlType="submit" block icon={<SendOutlined />}>
          Send transfer
        </Button>
      </Form>
    </Card>
  );
}
