import { Input } from 'antd';

export default function SearchBox({ value, onChange, placeholder }) {
  return (
    <Input.Search
      allowClear
      className="section-search"
      placeholder={placeholder}
      value={value}
      onChange={(event) => onChange(event.target.value)}
    />
  );
}
