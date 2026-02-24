import React, { useState, useMemo } from "react";
import { Form, Select, InputNumber, Button, Row, Col } from "antd";
import { SearchOutlined } from "@ant-design/icons";
import type { SearchRequest } from "../api/client";

/**
 * 城市-区域映射表
 * key 为城市名称，value 为该城市下的区域列表
 */
const CITY_DISTRICTS: Record<string, string[]> = {
  上海: [
    "浦东",
    "徐汇",
    "静安",
    "黄浦",
    "长宁",
    "闵行",
    "杨浦",
    "虹口",
    "普陀",
    "宝山",
    "松江",
    "嘉定",
  ],
  苏州: ["姑苏", "工业园区", "高新区", "吴中", "相城", "吴江"],
};

interface SearchFormProps {
  /** 搜索回调，将表单数据传递给父组件 */
  onSearch: (params: SearchRequest) => void;
  /** 是否处于加载状态 */
  loading: boolean;
}

/**
 * 搜索表单组件
 *
 * 提供城市、区域、价格范围筛选功能，区域选项根据城市动态变化。
 *
 * @author zhicheng.wang
 * @date 2026-02-24
 */
const SearchForm: React.FC<SearchFormProps> = ({ onSearch, loading }) => {
  const [form] = Form.useForm();
  const [selectedCity, setSelectedCity] = useState<string | undefined>(
    undefined
  );

  /** 根据选中城市动态获取区域列表 */
  const districtOptions = useMemo(() => {
    if (!selectedCity) return [];
    return (CITY_DISTRICTS[selectedCity] ?? []).map((d) => ({
      label: d,
      value: d,
    }));
  }, [selectedCity]);

  /** 城市变更时清空区域选择 */
  const handleCityChange = (city: string) => {
    setSelectedCity(city);
    form.setFieldValue("district", undefined);
  };

  /** 提交搜索表单 */
  const handleFinish = (values: {
    city: string;
    district?: string;
    price_min?: number;
    price_max?: number;
  }) => {
    const params: SearchRequest = {
      city: values.city,
      district: values.district,
      price_min: values.price_min ?? 0,
      price_max: values.price_max ?? 200000,
    };
    onSearch(params);
  };

  return (
    <Form
      form={form}
      layout="inline"
      onFinish={handleFinish}
      initialValues={{ price_min: 0, price_max: 200000 }}
    >
      <Row gutter={[16, 16]} style={{ width: "100%" }}>
        <Col xs={24} sm={12} md={6}>
          <Form.Item
            name="city"
            label="城市"
            rules={[{ required: true, message: "请选择城市" }]}
          >
            <Select
              placeholder="请选择城市"
              onChange={handleCityChange}
              allowClear
              options={Object.keys(CITY_DISTRICTS).map((c) => ({
                label: c,
                value: c,
              }))}
            />
          </Form.Item>
        </Col>

        <Col xs={24} sm={12} md={6}>
          <Form.Item name="district" label="区域">
            <Select
              placeholder="请选择区域"
              allowClear
              disabled={!selectedCity}
              options={districtOptions}
            />
          </Form.Item>
        </Col>

        <Col xs={24} sm={12} md={5}>
          <Form.Item name="price_min" label="最低价">
            <InputNumber
              style={{ width: "100%" }}
              min={0}
              step={1000}
              placeholder="最低单价"
              addonAfter="元/㎡"
            />
          </Form.Item>
        </Col>

        <Col xs={24} sm={12} md={5}>
          <Form.Item name="price_max" label="最高价">
            <InputNumber
              style={{ width: "100%" }}
              min={0}
              step={1000}
              placeholder="最高单价"
              addonAfter="元/㎡"
            />
          </Form.Item>
        </Col>

        <Col xs={24} sm={24} md={2}>
          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              icon={<SearchOutlined />}
              loading={loading}
              block
            >
              搜索
            </Button>
          </Form.Item>
        </Col>
      </Row>
    </Form>
  );
};

export default SearchForm;
