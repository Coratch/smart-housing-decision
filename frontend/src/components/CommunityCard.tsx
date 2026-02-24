import React from "react";
import { Card, Tag, Typography, Row, Col, Space } from "antd";
import type { CommunityBrief } from "../api/client";
import ScoreRadar from "./ScoreRadar";
import ProsCons from "./ProsCons";

const { Title, Text } = Typography;

interface CommunityCardProps {
  /** 小区简要信息 */
  community: CommunityBrief;
  /** 排名序号，从 1 开始 */
  rank: number;
}

/** 前三名使用金色徽章，其余使用灰色 */
const TOP_RANK_LIMIT = 3;

/**
 * 小区结果卡片组件
 *
 * 展示单个小区的搜索结果，包含排名、名称、区域、标签、均价、综合评分、
 * 五维雷达图和优缺点。
 *
 * @author zhicheng.wang
 * @date 2026-02-24
 */
const CommunityCard: React.FC<CommunityCardProps> = ({ community, rank }) => {
  const isTopRank = rank <= TOP_RANK_LIMIT;
  const rankColor = isTopRank ? "#faad14" : "#8c8c8c";
  const rankBgColor = isTopRank ? "#fff7e6" : "#f5f5f5";

  return (
    <Card
      hoverable
      style={{ marginBottom: 16 }}
      bodyStyle={{ padding: 20 }}
    >
      <Row gutter={[24, 16]} align="top">
        {/* 排名 + 基本信息 */}
        <Col xs={24} md={10}>
          <Space align="start" size={16}>
            {/* 排名徽章 */}
            <div
              style={{
                width: 40,
                height: 40,
                borderRadius: "50%",
                backgroundColor: rankBgColor,
                border: `2px solid ${rankColor}`,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                flexShrink: 0,
              }}
            >
              <Text strong style={{ color: rankColor, fontSize: 18 }}>
                {rank}
              </Text>
            </div>

            {/* 小区名称、位置、标签 */}
            <div>
              <Title level={4} style={{ margin: 0, marginBottom: 4 }}>
                {community.name}
              </Title>
              <Text type="secondary" style={{ fontSize: 13 }}>
                {community.city}
                {community.district ? `·${community.district}` : ""}
              </Text>

              {/* 标签 */}
              <div style={{ marginTop: 8 }}>
                {community.tags.map((tag) => (
                  <Tag color="blue" key={tag} style={{ marginBottom: 4 }}>
                    {tag}
                  </Tag>
                ))}
              </div>

              {/* 均价 */}
              {community.avg_price != null && (
                <div style={{ marginTop: 8 }}>
                  <Text type="secondary">均价 </Text>
                  <Text strong style={{ fontSize: 16, color: "#fa541c" }}>
                    {community.avg_price.toLocaleString()}
                  </Text>
                  <Text type="secondary"> 元/㎡</Text>
                </div>
              )}
            </div>
          </Space>
        </Col>

        {/* 综合评分 + 雷达图 */}
        <Col xs={24} md={8}>
          <div style={{ textAlign: "center" }}>
            <Text type="secondary" style={{ fontSize: 12 }}>
              综合评分
            </Text>
            <div>
              <Text
                strong
                style={{ fontSize: 36, color: "#1890ff", lineHeight: 1.2 }}
              >
                {community.score.toFixed(1)}
              </Text>
            </div>
          </div>
          <ScoreRadar subScores={community.sub_scores} />
        </Col>

        {/* 优缺点 */}
        <Col xs={24} md={6}>
          <div style={{ paddingTop: 8 }}>
            <Text
              strong
              type="secondary"
              style={{ fontSize: 12, marginBottom: 8, display: "block" }}
            >
              评价概要
            </Text>
            <ProsCons pros={community.pros} cons={community.cons} />
          </div>
        </Col>
      </Row>
    </Card>
  );
};

export default CommunityCard;
