"use client"

import { TrendingUp } from "lucide-react"
import { LabelList, Pie, PieChart } from "recharts"
import React, { memo } from "react"

import {
    Card,
    CardContent,
    CardDescription,
    CardFooter,
    CardHeader,
    CardTitle,
} from "@/components/ui/card"
import {
    ChartConfig,
    ChartContainer,
    ChartTooltip,
    ChartTooltipContent,
} from "@/components/ui/chart"

interface PieDataPoint {
    name: string
    value: number
    fill?: string
}

interface PieChartProps {
    data: PieDataPoint[]
    title?: string
    description?: string
    colors?: string[]
    showLabels?: boolean
    showTrend?: boolean
    trendText?: string
    className?: string
}

export const CustomPieChart = memo<PieChartProps>(function CustomPieChart({
    data,
    title,
    description,
    colors = ["var(--chart-1)", "var(--chart-2)", "var(--chart-3)", "var(--chart-4)", "var(--chart-5)"],
    showLabels = true,
    showTrend = false,
    trendText,
    className
}: PieChartProps) {
    // 数据验证
    if (!data || !Array.isArray(data) || data.length === 0) {
        throw new Error("饼图数据不能为空且必须是数组")
    }

    // 验证每个数据项
    const validatedData = data.filter((item, index) => {
        if (!item || typeof item !== 'object') {
            console.warn(`饼图数据第 ${index} 项无效:`, item)
            return false
        }
        if (!item.name || typeof item.name !== 'string') {
            console.warn(`饼图数据第 ${index} 项缺少有效的 name 字段:`, item)
            return false
        }
        if (typeof item.value !== 'number' || isNaN(item.value)) {
            console.warn(`饼图数据第 ${index} 项缺少有效的 value 字段:`, item)
            return false
        }
        return true
    })

    if (validatedData.length === 0) {
        throw new Error("饼图数据中没有有效的数据项")
    }

    // 为数据添加颜色
    const chartData = validatedData.map((item, index) => ({
        ...item,
        fill: item.fill || colors[index % colors.length]
    }))

    // 动态生成chartConfig，添加安全检查
    const chartConfig: ChartConfig = {
        value: {
            label: "Value",
        },
        ...validatedData.reduce((config, item, index) => {
            // 安全地处理 name 字段
            const safeName = item.name?.toString()?.toLowerCase() || `item_${index}`
            config[safeName] = {
                label: item.name || `项目 ${index + 1}`,
                color: colors[index % colors.length]
            }
            return config
        }, {} as ChartConfig)
    }

    return (
        <Card className={`flex flex-col ${className}`}>
            {(title || description) && (
                <CardHeader className="items-center pb-0">
                    {title && <CardTitle>{title}</CardTitle>}
                    {description && <CardDescription>{description}</CardDescription>}
                </CardHeader>
            )}
            <CardContent className="flex-1 pb-0">
                <ChartContainer
                    config={chartConfig}
                    className={`mx-auto aspect-square max-h-[250px] ${showLabels ? "[&_.recharts-text]:fill-background" : ""
                        }`}
                >
                    <PieChart>
                        <ChartTooltip
                            content={<ChartTooltipContent nameKey="value" hideLabel />}
                        />
                        <Pie data={chartData} dataKey="value">
                            {showLabels && (
                                <LabelList
                                    dataKey="name"
                                    className="fill-background"
                                    stroke="none"
                                    fontSize={12}
                                />
                            )}
                        </Pie>
                    </PieChart>
                </ChartContainer>
            </CardContent>
            {showTrend && (
                <CardFooter className="flex-col gap-2 text-sm">
                    <div className="flex items-center gap-2 leading-none font-medium">
                        {trendText || "数据趋势"} <TrendingUp className="h-4 w-4" />
                    </div>
                </CardFooter>
            )}
        </Card>
    )
}); 