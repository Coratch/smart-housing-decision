import React, { useMemo } from "react";
import ReactECharts from "echarts-for-react";
import type { SubScores } from "../api/client";

interface ScoreRadarProps {
  /** 五维子评分数据 */
  subScores: SubScores;
}

/**
 * 五维雷达图组件
 *
 * 使用 ECharts 渲染雷达图，展示小区在性价比、学区、配套、物业、开发商五个维度的评分。
 * 每个维度最高分为 10 分。
 *
 * @author zhicheng.wang
 * @date 2026-02-24
 */
const ScoreRadar: React.FC<ScoreRadarProps> = ({ subScores }) => {
  /** 雷达图维度标签与数据字段的映射 */
  const radarIndicators = useMemo(
    () => [
      { name: "性价比", max: 10 },
      { name: "学区", max: 10 },
      { name: "配套", max: 10 },
      { name: "物业", max: 10 },
      { name: "开发商", max: 10 },
    ],
    []
  );

  /** 按照维度顺序提取评分值 */
  const dataValues = useMemo(
    () => [
      subScores.price,
      subScores.school,
      subScores.facilities,
      subScores.property_mgmt,
      subScores.developer,
    ],
    [subScores]
  );

  const option = useMemo(
    () => ({
      radar: {
        indicator: radarIndicators,
        radius: "65%",
        axisName: {
          color: "#555",
          fontSize: 11,
        },
        splitNumber: 5,
        splitArea: {
          areaStyle: {
            color: ["#f5f7fa", "#eef1f6", "#e6eaf0", "#dde2ea", "#d5dbe4"],
          },
        },
      },
      series: [
        {
          type: "radar",
          data: [
            {
              value: dataValues,
              name: "评分",
              areaStyle: {
                color: "rgba(24, 144, 255, 0.25)",
              },
              lineStyle: {
                color: "#1890ff",
                width: 2,
              },
              itemStyle: {
                color: "#1890ff",
              },
            },
          ],
        },
      ],
      tooltip: {
        trigger: "item" as const,
      },
    }),
    [radarIndicators, dataValues]
  );

  return (
    <ReactECharts
      option={option}
      style={{ height: 220, width: "100%" }}
      opts={{ renderer: "svg" }}
    />
  );
};

export default ScoreRadar;
