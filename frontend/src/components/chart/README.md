# 图表组件库

基于 shadcn/ui 和 Recharts 构建的统一图表组件库，提供**极简的 API** 和丰富的图表类型。

## ✨ 核心特性

- 🎨 基于 shadcn/ui 设计系统
- 📊 支持 5 种常用图表类型：柱状图、折线图、面积图、饼图、雷达图
- 🚀 **极简接口**：只需 `type` 和 `data`，其他参数自动推断
- 🎯 **智能推断**：自动识别数据结构，无需指定字段名
- 🎨 内置美观的主题色彩
- 📱 响应式设计
- 🔧 向后兼容旧版本

## 🚀 快速开始

### 最简单的用法（推荐）

```tsx
import { Chart } from "@/components/chart"

// 只需要指定类型和数据，自动推断字段
<Chart type="bar" data={[
  { month: "Jan", desktop: 186, mobile: 80 },
  { month: "Feb", desktop: 305, mobile: 200 }
]} />

// 带标题
<Chart 
  type="pie" 
  data={[{ name: "Chrome", value: 275 }]}
  title="浏览器占比"
/>
```

### 便捷函数（更简洁）

```tsx
import { BarChart, LineChart, PieChart } from "@/components/chart"

// 函数式调用，更简洁
{BarChart(salesData, { title: "销售统计" })}
{LineChart(trendData, { showTrend: true })}
{PieChart(shareData, { showLabels: true })}
```

### 兼容旧版本

```tsx
// 仍然支持config包装方式
<Chart config={{
  type: "bar",
  data: chartData,
  title: "统计图表"
}} />
```

## 📊 支持的图表类型

### 1. 柱状图 (Bar Chart)

```tsx
// 自动推断版本
<Chart type="bar" data={salesData} title="销售数据" />

// 便捷函数版本
{BarChart(salesData, { 
  title: "销售数据",
  showTrend: true,
  trendText: "同比增长 12%" 
})}
```

### 2. 折线图 (Line Chart)

```tsx
<Chart type="line" data={trendData} title="趋势分析" />
{LineChart(trendData, { title: "趋势分析" })}
```

### 3. 面积图 (Area Chart)

```tsx
<Chart type="area" data={areaData} stacked={true} />
{AreaChart(areaData, { stacked: true, title: "累计数据" })}
```

### 4. 饼图 (Pie Chart)

```tsx
// 数据必须包含 name 和 value 字段
<Chart type="pie" data={[
  { name: "分类A", value: 400 },
  { name: "分类B", value: 300 }
]} />
{PieChart(pieData, { showLabels: true })}
```

### 5. 雷达图 (Radar Chart)

```tsx
<Chart type="radar" data={radarData} title="能力对比" />
{RadarChart(radarData, { title: "能力对比" })}
```

## 🎯 智能推断规则

### 自动字段识别

系统会自动分析数据结构：

1. **字符串字段** → 作为标签轴（X轴/角度轴）
2. **数值字段** → 作为数据系列（Y轴）
3. **饼图特殊处理** → 必须有 `name` 和 `value` 字段

```tsx
// 这些数据会被自动识别
const data = [
  { month: "Jan", sales: 100, profit: 50 },  // month→X轴, sales&profit→Y轴
  { category: "A", value1: 200, value2: 150 } // category→X轴, value1&value2→Y轴
]

const pieData = [
  { name: "Chrome", value: 65 }  // 饼图标准格式，自动识别
]
```

## 📋 配置参数

### 必需参数

| 参数 | 类型 | 描述 |
|------|------|------|
| `type` | `"bar" \| "line" \| "area" \| "pie" \| "radar"` | 图表类型 |
| `data` | `Array<object>` | 图表数据 |

### 可选参数

| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `title` | `string` | - | 图表标题 |
| `description` | `string` | - | 图表描述 |
| `showTrend` | `boolean` | `false` | 显示趋势信息 |
| `trendText` | `string` | "数据趋势" | 自定义趋势文本 |
| `stacked` | `boolean` | `false` | 是否堆叠（仅面积图） |
| `showLabels` | `boolean` | `true` | 是否显示标签（仅饼图） |
| `colors` | `string[]` | 默认主题色 | 自定义颜色数组 |
| `className` | `string` | - | 自定义CSS类名 |

### 高级参数（手动覆盖）

如果自动推断不满足需求，可以手动指定：

| 参数 | 适用图表 | 描述 |
|------|----------|------|
| `xKey` | bar, line, area | 手动指定X轴字段 |
| `yKeys` | bar, line, area, radar | 手动指定Y轴字段数组 |
| `angleKey` | radar | 手动指定雷达图角度字段 |

## 💡 使用示例

### 完整的仪表板

```tsx
import { Chart, BarChart, LineChart, PieChart } from "@/components/chart"

function Dashboard() {
  const salesData = [
    { month: "Jan", revenue: 1200, profit: 400 },
    { month: "Feb", revenue: 1800, profit: 600 },
    { month: "Mar", revenue: 1500, profit: 500 },
  ]

  const browserData = [
    { name: "Chrome", value: 65 },
    { name: "Firefox", value: 20 },
    { name: "Safari", value: 15 },
  ]

  return (
    <div className="grid grid-cols-2 gap-6">
      {/* 方式1: 统一接口 */}
      <Chart 
        type="line" 
        data={salesData}
        title="收入趋势"
        showTrend={true}
      />

      {/* 方式2: 便捷函数 */}
      {PieChart(browserData, {
        title: "浏览器占比",
        showLabels: true
      })}

      {/* 方式3: 最简用法 */}
      <Chart type="bar" data={salesData} />
      
      {/* 方式4: 兼容旧版本 */}
      <Chart config={{
        type: "area",
        data: salesData,
        stacked: true
      }} />
    </div>
  )
}
```

### 不同调用方式对比

```tsx
// ❌ 旧版本 - 复杂
<Chart config={{
  type: "bar",
  data: salesData,
  title: "销售统计",
  xKey: "month",
  yKeys: ["revenue", "profit"],
  showTrend: true
}} />

// ✅ 新版本 - 简化
<Chart 
  type="bar" 
  data={salesData}
  title="销售统计"
  showTrend={true}
/>

// ✅ 便捷函数 - 更简洁
{BarChart(salesData, {
  title: "销售统计",
  showTrend: true
})}

// ✅ 极简版本
<Chart type="bar" data={salesData} />
```

## 🎨 主题定制

图表使用 CSS 变量进行主题控制：

```css
:root {
  --chart-1: 220 70% 50%;   /* 蓝色 */
  --chart-2: 160 60% 45%;   /* 绿色 */
  --chart-3: 30 80% 55%;    /* 橙色 */
  --chart-4: 280 65% 60%;   /* 紫色 */
  --chart-5: 340 75% 55%;   /* 粉色 */
}
```

### 自定义颜色

```tsx
<Chart 
  type="bar" 
  data={data}
  colors={["#FF6B6B", "#4ECDC4", "#45B7D1"]}
/>
```

## 📱 响应式设计

```tsx
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
  <Chart type="bar" data={data1} />
  <Chart type="line" data={data2} />
  <Chart type="pie" data={data3} />
</div>
```

## 🔧 数据格式要求

### 通用图表格式

```typescript
// ✅ 正确格式：至少一个字符串字段 + 一个数值字段
const data = [
  { label: "A", value1: 100, value2: 200 },
  { category: "B", sales: 150, profit: 80 },
  { name: "C", count: 300, rate: 85 }
]

// ❌ 错误格式：缺少字符串标签字段
const badData = [
  { value1: 100, value2: 200 },  // 没有字符串字段
]
```

### 饼图格式

```typescript
// ✅ 正确格式：必须有 name 和 value
const pieData = [
  { name: "分类A", value: 100 },
  { name: "分类B", value: 200 }
]

// ❌ 错误格式
const badPieData = [
  { label: "A", count: 100 }  // 不是 name/value 字段
]
```

## 🛠️ 最佳实践

1. **优先使用简化接口**：让系统自动推断字段，减少配置
2. **数据准备**：确保数据格式符合要求
3. **性能优化**：大数据集考虑分页处理
4. **颜色一致性**：使用统一的色彩方案
5. **响应式测试**：在不同屏幕尺寸下验证效果

## 📚 API 参考

### Chart 组件

```typescript
// 新版本简化接口
interface ChartProps {
  type: ChartType
  data: DataPoint[] | PieDataPoint[]
  title?: string
  description?: string
  xKey?: string        // 可选，自动推断
  yKeys?: string[]     // 可选，自动推断  
  angleKey?: string    // 可选，自动推断
  colors?: string[]
  stacked?: boolean
  showLabels?: boolean
  showTrend?: boolean
  trendText?: string
  className?: string
}

// 兼容旧版本
interface ChartConfig {
  config: ChartProps
}
```

### 便捷函数

```typescript
BarChart(data: DataPoint[], options?: Omit<ChartProps, 'type' | 'data'>)
LineChart(data: DataPoint[], options?: Omit<ChartProps, 'type' | 'data'>)
AreaChart(data: DataPoint[], options?: Omit<ChartProps, 'type' | 'data'>)
PieChart(data: PieDataPoint[], options?: Omit<ChartProps, 'type' | 'data'>)
RadarChart(data: DataPoint[], options?: Omit<ChartProps, 'type' | 'data'>)
``` 