"use client"

import { Chart, type ChartConfig } from "./index"

/**
 * 快速创建柱状图
 * @param data 数据数组，每个对象应包含 name 和至少一个数值字段
 * @param options 可选配置
 */
export function BarChart(
    data: Array<Record<string, string | number>>,
    options?: {
        title?: string
        description?: string
        showTrend?: boolean
        trendText?: string
    }
) {
    // 自动检测数据结构
    if (!data || data.length === 0) {
        throw new Error("数据不能为空")
    }

    const firstItem = data[0]
    const keys = Object.keys(firstItem)

    // 找到第一个字符串字段作为 xKey
    const xKey = keys.find(key => typeof firstItem[key] === 'string')
    if (!xKey) {
        throw new Error("数据中需要至少包含一个字符串字段作为标签")
    }

    // 其余数值字段作为 yKeys
    const yKeys = keys.filter(key => key !== xKey && typeof firstItem[key] === 'number')
    if (yKeys.length === 0) {
        throw new Error("数据中需要至少包含一个数值字段")
    }

    const config: ChartConfig = {
        type: "bar",
        data,
        xKey,
        yKeys,
        ...options
    }

    return <Chart config={config} />
}

/**
 * 快速创建折线图
 */
export function LineChart(
    data: Array<Record<string, string | number>>,
    options?: {
        title?: string
        description?: string
        showTrend?: boolean
        trendText?: string
    }
) {
    if (!data || data.length === 0) {
        throw new Error("数据不能为空")
    }

    const firstItem = data[0]
    const keys = Object.keys(firstItem)

    const xKey = keys.find(key => typeof firstItem[key] === 'string')
    if (!xKey) {
        throw new Error("数据中需要至少包含一个字符串字段作为标签")
    }

    const yKeys = keys.filter(key => key !== xKey && typeof firstItem[key] === 'number')
    if (yKeys.length === 0) {
        throw new Error("数据中需要至少包含一个数值字段")
    }

    const config: ChartConfig = {
        type: "line",
        data,
        xKey,
        yKeys,
        ...options
    }

    return <Chart config={config} />
}

/**
 * 快速创建面积图
 */
export function AreaChart(
    data: Array<Record<string, string | number>>,
    options?: {
        title?: string
        description?: string
        stacked?: boolean
        showTrend?: boolean
        trendText?: string
    }
) {
    if (!data || data.length === 0) {
        throw new Error("数据不能为空")
    }

    const firstItem = data[0]
    const keys = Object.keys(firstItem)

    const xKey = keys.find(key => typeof firstItem[key] === 'string')
    if (!xKey) {
        throw new Error("数据中需要至少包含一个字符串字段作为标签")
    }

    const yKeys = keys.filter(key => key !== xKey && typeof firstItem[key] === 'number')
    if (yKeys.length === 0) {
        throw new Error("数据中需要至少包含一个数值字段")
    }

    const config: ChartConfig = {
        type: "area",
        data,
        xKey,
        yKeys,
        stacked: options?.stacked || false,
        title: options?.title,
        description: options?.description,
        showTrend: options?.showTrend,
        trendText: options?.trendText
    }

    return <Chart config={config} />
}

/**
 * 快速创建饼图
 * @param data 数据数组，每个对象应包含 name 和 value 字段
 */
export function PieChart(
    data: Array<{ name: string; value: number }>,
    options?: {
        title?: string
        description?: string
        showLabels?: boolean
        showTrend?: boolean
        trendText?: string
    }
) {
    if (!data || data.length === 0) {
        throw new Error("数据不能为空")
    }

    const config: ChartConfig = {
        type: "pie",
        data,
        showLabels: options?.showLabels ?? true,
        ...options
    }

    return <Chart config={config} />
}

/**
 * 快速创建雷达图
 */
export function RadarChart(
    data: Array<Record<string, string | number>>,
    options?: {
        title?: string
        description?: string
        showTrend?: boolean
        trendText?: string
    }
) {
    if (!data || data.length === 0) {
        throw new Error("数据不能为空")
    }

    const firstItem = data[0]
    const keys = Object.keys(firstItem)

    const angleKey = keys.find(key => typeof firstItem[key] === 'string')
    if (!angleKey) {
        throw new Error("数据中需要至少包含一个字符串字段作为角度标签")
    }

    const yKeys = keys.filter(key => key !== angleKey && typeof firstItem[key] === 'number')
    if (yKeys.length === 0) {
        throw new Error("数据中需要至少包含一个数值字段")
    }

    const config: ChartConfig = {
        type: "radar",
        data,
        angleKey,
        yKeys,
        ...options
    }

    return <Chart config={config} />
} 