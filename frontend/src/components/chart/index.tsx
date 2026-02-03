"use client"

import { CustomAreaChart } from "./area-chart"
import { CustomBarChart } from "./bar-chart"
import { CustomLineChart } from "./line-chart"
import { CustomPieChart } from "./pie-chart"
import { CustomRadarChart } from "./radar-chart"
import ChartErrorBoundary, { withChartErrorBoundary } from "./error-boundary"
import { AlertCircle } from "lucide-react"
import React, { memo } from "react"

// 通用数据点接口
interface DataPoint {
    [key: string]: string | number
}

// 饼图数据点接口
interface PieDataPoint {
    name: string
    value: number
    fill?: string
}

// 图表类型枚举
type ChartType = "area" | "bar" | "line" | "pie" | "radar"

// 简化的图表配置接口
interface ChartProps {
    type: ChartType
    data: DataPoint[] | PieDataPoint[]
    title?: string
    description?: string
    // 可选的手动指定字段，如果不指定则自动推断
    xKey?: string
    yKeys?: string[]
    angleKey?: string
    // 样式配置
    colors?: string[]
    stacked?: boolean // 仅面积图
    showLabels?: boolean // 仅饼图
    showTrend?: boolean
    trendText?: string
    className?: string
}

// 兼容旧版本的config接口
interface ChartConfig {
    config: ChartProps
}

// 默认颜色配置
const DEFAULT_COLORS = [
    "var(--chart-1)",
    "var(--chart-2)",
    "var(--chart-3)",
    "var(--chart-4)",
    "var(--chart-5)"
]

/**
 * 安全地获取对象的键
 */
function safeObjectKeys(obj: any): string[] {
    if (!obj || typeof obj !== 'object') {
        return []
    }
    try {
        return Object.keys(obj)
    } catch {
        return []
    }
}

/**
 * 验证数据项的完整性
 */
function validateDataItem(item: any, index: number, type: ChartType): boolean {
    if (!item || typeof item !== 'object') {
        console.warn(`第 ${index} 项数据无效:`, item)
        return false
    }

    const keys = safeObjectKeys(item)
    if (keys.length === 0) {
        console.warn(`第 ${index} 项数据为空对象:`, item)
        return false
    }

    // 饼图特殊验证
    if (type === "pie") {
        if (!item.name || typeof item.name !== 'string') {
            console.warn(`饼图第 ${index} 项缺少有效的 name 字段:`, item)
            return false
        }
        if (typeof item.value !== 'number' || isNaN(item.value)) {
            console.warn(`饼图第 ${index} 项缺少有效的 value 字段:`, item)
            return false
        }
        return true
    }

    // 其他图表类型验证至少有一个字符串和一个数字字段
    const hasStringField = keys.some(key => {
        const value = item[key]
        return value !== null && value !== undefined && typeof value === 'string' && value.length > 0
    })

    const hasNumberField = keys.some(key => {
        const value = item[key]
        return typeof value === 'number' && !isNaN(value)
    })

    if (!hasStringField) {
        console.warn(`第 ${index} 项数据缺少有效的字符串字段:`, item)
        return false
    }

    if (!hasNumberField) {
        console.warn(`第 ${index} 项数据缺少有效的数值字段:`, item)
        return false
    }

    return true
}

/**
 * 自动推断数据结构
 */
function inferDataStructure(data: any[], type: ChartType) {
    // 基础验证
    if (!data) {
        throw new Error("数据不能为空")
    }

    if (!Array.isArray(data)) {
        throw new Error("数据必须是数组格式")
    }

    if (data.length === 0) {
        throw new Error("数据数组不能为空")
    }

    // 过滤并验证数据项
    const validData = data.filter((item, index) => validateDataItem(item, index, type))

    if (validData.length === 0) {
        throw new Error("没有有效的数据项")
    }

    if (validData.length < data.length) {
        console.warn(`原始数据 ${data.length} 项，有效数据 ${validData.length} 项`)
    }

    const firstItem = validData[0]
    const keys = safeObjectKeys(firstItem)

    // 饼图特殊处理
    if (type === "pie") {
        // 已在 validateDataItem 中验证过
        return { xKey: undefined, yKeys: undefined, angleKey: undefined }
    }

    // 找到字符串字段作为标签
    const stringKey = keys.find(key => {
        const value = firstItem[key]
        return value !== null && value !== undefined && typeof value === 'string' && value.length > 0
    })

    if (!stringKey) {
        throw new Error("数据中需要至少包含一个有效的字符串字段作为标签")
    }

    // 找到数值字段作为数据系列
    const numberKeys = keys.filter(key => {
        if (key === stringKey) return false
        const value = firstItem[key]
        return typeof value === 'number' && !isNaN(value)
    })

    if (numberKeys.length === 0) {
        throw new Error("数据中需要至少包含一个有效的数值字段")
    }

    return {
        xKey: type === "radar" ? undefined : stringKey,
        yKeys: numberKeys,
        angleKey: type === "radar" ? stringKey : undefined
    }
}

/**
 * 简化的统一图表组件
 * 
 * @param props 图表配置 - 只需要 type 和 data，其他参数自动推断
 * @returns 对应的图表组件
 * 
 * 使用示例：
 * // 最简单的用法 - 只需要指定类型和数据
 * <Chart type="bar" data={[{ month: "Jan", sales: 100, profit: 50 }]} />
 * 
 * // 带标题
 * <Chart type="pie" data={[{ name: "Chrome", value: 275 }]} title="浏览器占比" />
 * 
 * // 完整配置
 * <Chart 
 *   type="line" 
 *   data={chartData} 
 *   title="趋势分析"
 *   showTrend={true}
 *   trendText="呈上升趋势"
 * />
 * 
 * // 兼容旧版本 config 方式
 * <Chart config={{ type: "bar", data: chartData }} />
 */
export const Chart = memo<ChartProps | ChartConfig>(function Chart(props: ChartProps | ChartConfig) {
    // 兼容两种调用方式：新的直接props和旧的config包装
    let config: ChartProps

    try {
        config = 'config' in props ? props.config : props

        // 基础配置验证
        if (!config || typeof config !== 'object') {
            throw new Error("图表配置无效")
        }

        if (!config.type) {
            throw new Error("图表类型不能为空")
        }

        if (!config.data) {
            throw new Error("图表数据不能为空")
        }
    } catch (error: any) {
        console.error("图表配置错误:", error)
        return (
            <div className={`flex flex-col items-center justify-center p-4 border border-red-300 bg-red-50 rounded-md`}>
                <AlertCircle className="w-6 h-6 text-red-500 mb-2" />
                <p className="text-sm text-red-700">图表配置错误</p>
                <p className="text-xs text-red-600 mt-1">错误信息: {error.message || '配置对象无效'}</p>
            </div>
        )
    }

    const {
        type,
        data,
        title,
        description,
        xKey: manualXKey,
        yKeys: manualYKeys,
        angleKey: manualAngleKey,
        colors = DEFAULT_COLORS,
        stacked = false,
        showLabels = true,
        showTrend = false,
        trendText,
        className
    } = config

    try {
        // 自动推断数据结构（如果没有手动指定）
        const inferred = inferDataStructure(data, type)
        const xKey = manualXKey || inferred.xKey
        const yKeys = manualYKeys || inferred.yKeys
        const angleKey = manualAngleKey || inferred.angleKey

        const commonProps = {
            title,
            description,
            colors,
            showTrend,
            trendText,
            className
        }

        switch (type) {
            case "area":
                return (
                    <CustomAreaChart
                        data={data as DataPoint[]}
                        xKey={xKey!}
                        yKeys={yKeys!}
                        stacked={stacked}
                        {...commonProps}
                    />
                )

            case "bar":
                return (
                    <CustomBarChart
                        data={data as DataPoint[]}
                        xKey={xKey!}
                        yKeys={yKeys!}
                        {...commonProps}
                    />
                )

            case "line":
                return (
                    <CustomLineChart
                        data={data as DataPoint[]}
                        xKey={xKey!}
                        yKeys={yKeys!}
                        {...commonProps}
                    />
                )

            case "pie":
                return (
                    <CustomPieChart
                        data={data as PieDataPoint[]}
                        showLabels={showLabels}
                        {...commonProps}
                    />
                )

            case "radar":
                return (
                    <CustomRadarChart
                        data={data as DataPoint[]}
                        angleKey={angleKey!}
                        yKeys={yKeys!}
                        {...commonProps}
                    />
                )

            default:
                // 如果传入不支持的图表类型
                return (
                    <div className={`flex flex-col items-center justify-center p-4 border border-red-300 bg-red-50 rounded-md ${className}`}>
                        <AlertCircle className="w-6 h-6 text-red-500 mb-2" />
                        <p className="text-sm text-red-700">不支持的图表类型: {type}</p>
                        {title && <p className="text-xs text-red-600 mt-1">图表标题: {title}</p>}
                    </div>
                );
        }
    } catch (error: any) {
        // 捕获推断数据结构或渲染子组件时发生的错误
        console.error("图表渲染错误:", error);

        // 确保错误信息是字符串
        const errorMessage = error?.message || error?.toString() || '未知错误'

        return (
            <div className={`flex flex-col items-center justify-center p-4 border border-red-300 bg-red-50 rounded-md ${className}`}>
                <AlertCircle className="w-6 h-6 text-red-500 mb-2" />
                <p className="text-sm text-red-700 font-medium">图表渲染失败</p>
                {title && <p className="text-sm text-red-600 mt-1">图表: {title}</p>}
                <p className="text-xs text-red-600 mt-2 text-center max-w-md">
                    {errorMessage}
                </p>

                {/* 在开发环境显示详细错误信息 */}
                {process.env.NODE_ENV === 'development' && error?.stack && (
                    <details className="mt-3 w-full max-w-md">
                        <summary className="text-xs text-red-500 cursor-pointer">
                            详细错误信息 (开发模式)
                        </summary>
                        <pre className="mt-2 text-xs text-red-600 bg-red-100 p-2 rounded overflow-auto max-h-32 whitespace-pre-wrap">
                            {error.stack}
                        </pre>
                    </details>
                )}

                {/* 提供重试建议 */}
                <div className="mt-3 text-xs text-red-500 text-center">
                    <p>请检查数据格式是否正确</p>
                    <p>建议使用 ChartErrorBoundary 或 SafeChart 组件</p>
                </div>
            </div>
        );
    }
}, (prevProps, nextProps) => {
    // 自定义比较函数：深度比较图表相关的属性
    const prevConfig = 'config' in prevProps ? prevProps.config : prevProps;
    const nextConfig = 'config' in nextProps ? nextProps.config : nextProps;

    // 比较所有重要的图表属性
    return (
        prevConfig.type === nextConfig.type &&
        prevConfig.title === nextConfig.title &&
        prevConfig.description === nextConfig.description &&
        prevConfig.xKey === nextConfig.xKey &&
        prevConfig.angleKey === nextConfig.angleKey &&
        prevConfig.stacked === nextConfig.stacked &&
        prevConfig.showLabels === nextConfig.showLabels &&
        prevConfig.showTrend === nextConfig.showTrend &&
        prevConfig.trendText === nextConfig.trendText &&
        prevConfig.className === nextConfig.className &&
        JSON.stringify(prevConfig.data) === JSON.stringify(nextConfig.data) &&
        JSON.stringify(prevConfig.yKeys) === JSON.stringify(nextConfig.yKeys) &&
        JSON.stringify(prevConfig.colors) === JSON.stringify(nextConfig.colors)
    );
});

// 更简洁的便捷函数
export const BarChart = (data: DataPoint[], options?: Omit<ChartProps, 'type' | 'data'>) =>
    <Chart type="bar" data={data} {...options} />

export const LineChart = (data: DataPoint[], options?: Omit<ChartProps, 'type' | 'data'>) =>
    <Chart type="line" data={data} {...options} />

export const AreaChart = (data: DataPoint[], options?: Omit<ChartProps, 'type' | 'data'>) =>
    <Chart type="area" data={data} {...options} />

export const PieChart = (data: PieDataPoint[], options?: Omit<ChartProps, 'type' | 'data'>) =>
    <Chart type="pie" data={data} {...options} />

export const RadarChart = (data: DataPoint[], options?: Omit<ChartProps, 'type' | 'data'>) =>
    <Chart type="radar" data={data} {...options} />

// 创建带有错误边界的安全图表组件
export const SafeChart = withChartErrorBoundary(Chart)
export const SafeAreaChart = withChartErrorBoundary(CustomAreaChart)
export const SafeBarChart = withChartErrorBoundary(CustomBarChart)
export const SafeLineChart = withChartErrorBoundary(CustomLineChart)
export const SafePieChart = withChartErrorBoundary(CustomPieChart)
export const SafeRadarChart = withChartErrorBoundary(CustomRadarChart)

// 导出所有单独的图表组件，以便直接使用
export {
    CustomAreaChart,
    CustomBarChart,
    CustomLineChart,
    CustomPieChart,
    CustomRadarChart,
    ChartErrorBoundary,
    withChartErrorBoundary
}

// 导出类型定义
export type { ChartProps as ChartConfig, DataPoint, PieDataPoint, ChartType } 