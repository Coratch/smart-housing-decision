import React, { useState } from "react";
import { Layout, Typography, Card, Empty, Spin, message } from "antd";
import SearchForm from "../components/SearchForm";
import CommunityCard from "../components/CommunityCard";
import {
  searchCommunities,
  type SearchRequest,
  type CommunityBrief,
} from "../api/client";

const { Header, Content } = Layout;
const { Title, Text } = Typography;

/**
 * 搜索主页面
 *
 * 包含页头、搜索表单、搜索结果列表。用户提交搜索后调用后端接口，
 * 将返回的小区列表以卡片形式展示。
 *
 * @author zhicheng.wang
 * @date 2026-02-24
 */
const SearchPage: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<CommunityBrief[]>([]);
  const [searched, setSearched] = useState(false);

  /** 处理搜索请求 */
  const handleSearch = async (params: SearchRequest) => {
    setLoading(true);
    setSearched(true);
    try {
      const response = await searchCommunities(params);
      setResults(response.data.communities);
      if (response.data.communities.length === 0) {
        message.info("未找到符合条件的小区，请调整筛选条件后重试");
      }
    } catch (error: unknown) {
      const errorMessage =
        error instanceof Error ? error.message : "未知错误";
      message.error(`搜索失败: ${errorMessage}`);
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout style={{ minHeight: "100vh", background: "#f0f2f5" }}>
      {/* 页头 */}
      <Header
        style={{
          background: "#001529",
          display: "flex",
          alignItems: "center",
          padding: "0 24px",
        }}
      >
        <Title level={3} style={{ color: "#fff", margin: 0 }}>
          智慧购房决策工具
        </Title>
      </Header>

      {/* 主内容区 */}
      <Content style={{ padding: "24px", maxWidth: 1200, margin: "0 auto", width: "100%" }}>
        {/* 搜索表单 */}
        <Card style={{ marginBottom: 24 }}>
          <SearchForm onSearch={handleSearch} loading={loading} />
        </Card>

        {/* 搜索结果 */}
        {loading ? (
          <div style={{ textAlign: "center", padding: "60px 0" }}>
            <Spin size="large" />
            <div style={{ marginTop: 16 }}>
              <Text type="secondary">正在智能分析中，请稍候...</Text>
            </div>
          </div>
        ) : searched && results.length === 0 ? (
          <Empty
            description="未找到符合条件的小区"
            style={{ padding: "60px 0" }}
          />
        ) : (
          <>
            {results.length > 0 && (
              <div style={{ marginBottom: 16 }}>
                <Text type="secondary">
                  共找到 <Text strong>{results.length}</Text> 个小区
                </Text>
              </div>
            )}
            {results.map((community, index) => (
              <CommunityCard
                key={community.id}
                community={community}
                rank={index + 1}
              />
            ))}
          </>
        )}
      </Content>
    </Layout>
  );
};

export default SearchPage;
