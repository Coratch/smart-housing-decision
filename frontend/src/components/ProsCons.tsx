import React from "react";
import { Space, Typography } from "antd";
import { CheckCircleOutlined, CloseCircleOutlined } from "@ant-design/icons";

const { Text } = Typography;

/** 展示的最大优点/缺点条数 */
const MAX_DISPLAY_COUNT = 2;

interface ProsConsProps {
  /** 优点列表 */
  pros: string[];
  /** 缺点列表 */
  cons: string[];
}

/**
 * 优缺点展示组件
 *
 * 以绿色对勾展示优点、红色叉号展示缺点，各最多显示 2 条。
 *
 * @author zhicheng.wang
 * @date 2026-02-24
 */
const ProsCons: React.FC<ProsConsProps> = ({ pros, cons }) => {
  const displayPros = pros.slice(0, MAX_DISPLAY_COUNT);
  const displayCons = cons.slice(0, MAX_DISPLAY_COUNT);

  return (
    <Space direction="vertical" size={4} style={{ width: "100%" }}>
      {displayPros.map((text, index) => (
        <Text key={`pro-${index}`} style={{ fontSize: 13 }}>
          <CheckCircleOutlined style={{ color: "#52c41a", marginRight: 6 }} />
          {text}
        </Text>
      ))}
      {displayCons.map((text, index) => (
        <Text key={`con-${index}`} style={{ fontSize: 13 }}>
          <CloseCircleOutlined style={{ color: "#ff4d4f", marginRight: 6 }} />
          {text}
        </Text>
      ))}
    </Space>
  );
};

export default ProsCons;
