"use client"

import { Chart, AreaChart, PieChart, RadarChart } from "./index"

// 演示数据
const salesData = [
    { month: "1月", desktop: 186, mobile: 80 },
    { month: "2月", desktop: 305, mobile: 200 },
    { month: "3月", desktop: 237, mobile: 120 },
    { month: "4月", desktop: 73, mobile: 190 },
    { month: "5月", desktop: 209, mobile: 130 },
    { month: "6月", desktop: 214, mobile: 140 },
]

const browserData = [
    { name: "Chrome", value: 275 },
    { name: "Safari", value: 200 },
    { name: "Firefox", value: 187 },
    { name: "Edge", value: 173 },
    { name: "其他", value: 90 },
]

const performanceData = [
    { 能力: "编程", 前端: 120, 后端: 110 },
    { 能力: "设计", 前端: 98, 后端: 130 },
    { 能力: "测试", 前端: 86, 后端: 130 },
    { 能力: "部署", 前端: 99, 后端: 100 },
    { 能力: "文档", 前端: 85, 后端: 90 },
]

/**
 * 简化接口演示组件
 * 展示极简的图表使用方法
 */
export function SimpleChartDemo() {
    return (
        <div className="p-6 space-y-8">
            <div className="text-center">
                <h1 className="text-3xl font-bold mb-4">简化图表接口演示</h1>
                <p className="text-gray-600">无需指定字段名，自动推断数据结构</p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* 最简单的用法 - 只传数据和类型 */}
                <Chart type="bar" data={salesData} />

                {/* 带标题的简单用法 */}
                <Chart
                    type="line"
                    data={salesData}
                    title="访问趋势"
                    description="桌面端与移动端访问量变化"
                />

                {/* 使用便捷函数 - 更简洁 */}
                {AreaChart(salesData, {
                    title: "累计访问量",
                    stacked: true,
                    showTrend: true,
                    trendText: "整体呈上升趋势"
                })}

                {/* 饼图 - 自动识别 name 和 value */}
                {PieChart(browserData, {
                    title: "浏览器市场份额",
                    showLabels: true
                })}

                {/* 雷达图 - 跨列显示 */}
                <div className="lg:col-span-2">
                    {RadarChart(performanceData, {
                        title: "团队能力对比",
                        description: "前端团队 vs 后端团队各项能力评估"
                    })}
                </div>
            </div>

            {/* 对比：新旧接口方式 */}
            <div className="mt-12 space-y-6">
                <h2 className="text-2xl font-semibold">接口对比</h2>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* 旧版本复杂接口 */}
                    <div className="p-4 bg-red-50 rounded-lg">
                        <h3 className="font-semibold text-red-800 mb-3">旧版本（复杂）</h3>
                        <pre className="text-xs bg-white p-3 rounded overflow-x-auto">
                            {`<Chart config={{
  type: "bar",
  data: salesData,
  title: "销售统计",
  xKey: "month",
  yKeys: ["desktop", "mobile"],
  showTrend: true
}} />`}
                        </pre>
                    </div>

                    {/* 新版本简化接口 */}
                    <div className="p-4 bg-green-50 rounded-lg">
                        <h3 className="font-semibold text-green-800 mb-3">新版本（简化）</h3>
                        <pre className="text-xs bg-white p-3 rounded overflow-x-auto">
                            {`<Chart 
  type="bar" 
  data={salesData}
  title="销售统计"
  showTrend={true}
/>

// 或便捷函数
{BarChart(salesData, {
  title: "销售统计",
  showTrend: true
})}`}
                        </pre>
                    </div>
                </div>

                <div className="bg-blue-50 p-4 rounded-lg">
                    <h3 className="font-semibold text-blue-800 mb-2">✨ 简化特性</h3>
                    <ul className="text-sm text-blue-700 space-y-1">
                        <li>• <strong>自动推断字段</strong>：无需手动指定 xKey、yKeys、angleKey</li>
                        <li>• <strong>智能数据识别</strong>：自动区分字符串标签和数值数据</li>
                        <li>• <strong>便捷函数</strong>：提供 BarChart、LineChart 等直接函数</li>
                        <li>• <strong>向后兼容</strong>：支持旧版本 config 包装方式</li>
                        <li>• <strong>类型安全</strong>：完整的 TypeScript 类型支持</li>
                    </ul>
                </div>

                <div className="bg-yellow-50 p-4 rounded-lg">
                    <h3 className="font-semibold text-yellow-800 mb-2">📋 数据格式要求</h3>
                    <div className="text-sm text-yellow-700 space-y-2">
                        <div>
                            <strong>普通图表：</strong>至少包含一个字符串字段（作为标签）和一个数值字段
                        </div>
                        <div>
                            <strong>饼图：</strong>必须包含 name 和 value 字段
                        </div>
                        <div className="mt-2">
                            <pre className="bg-white p-2 rounded text-xs">
                                {`// 通用格式
[{ label: "A", value1: 100, value2: 200 }]

// 饼图格式  
[{ name: "分类A", value: 100 }]`}
                            </pre>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
} 