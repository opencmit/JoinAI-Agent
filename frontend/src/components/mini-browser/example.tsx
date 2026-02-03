"use client";

import React from "react";
import { MiniBrowser } from "./mini-browser";

export function MiniBrowserExample() {
  return (
    <div className="space-y-1 p-6">
      <h2 className="text-2xl font-bold">Mini Browser 组件示例</h2>
      
      {/* 基本用法 */}
      <div className="space-y-0">
        <h3 className="text-lg font-semibold">基本用法 - 允许用户输入网址</h3>
        <MiniBrowser
          url="https://www.google.com"
          height="300px"
          onUrlChange={(url) => console.log("网址变化:", url)}
          onRefresh={() => console.log("页面刷新")}
        />
      </div>
      
      {/* 禁用输入 */}
      <div className="space-y-2">
        <h3 className="text-lg font-semibold">禁用用户输入 - 只能查看指定网址</h3>
        <MiniBrowser
          url="https://www.github.com"
          disableUrlInput={true}
          height="300px"
          onRefresh={() => console.log("页面刷新")}
        />
      </div>
      
      {/* 自定义高度 */}
      <div className="space-y-2">
        <h3 className="text-lg font-semibold">自定义高度</h3>
        <MiniBrowser
          url="https://www.wikipedia.org"
          height="500px"
          className="border-2 border-blue-200"
        />
      </div>
    </div>
  );
}

export default MiniBrowserExample; 