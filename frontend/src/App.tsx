import React from "react";
import SearchPage from "./pages/SearchPage";

/**
 * 应用根组件
 *
 * 当前直接渲染搜索主页面，后续可扩展为路由模式。
 *
 * @author zhicheng.wang
 * @date 2026-02-24
 */
const App: React.FC = () => {
  return <SearchPage />;
};

export default App;
