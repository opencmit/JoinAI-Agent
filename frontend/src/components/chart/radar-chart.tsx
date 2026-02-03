"use client"

import { TrendingUp } from "lucide-react"
import { PolarAngleAxis, PolarGrid, Radar, RadarChart } from "recharts"
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

interface DataPoint {
    [key: string]: string | number
}

interface RadarChartProps {
    data: DataPoint[]
    title?: string
    description?: string
    angleKey: string
    yKeys: string[]
    colors?: string[]
    showTrend?: boolean
    trendText?: string
    className?: string
}

export const CustomRadarChart = memo<RadarChartProps>(function CustomRadarChart({
    data,
    title,
    description,
    angleKey,
    yKeys,
    colors = ["var(--chart-1)", "var(--chart-2)", "var(--chart-3)", "var(--chart-4)", "var(--chart-5)"],
    showTrend = false,
    trendText,
    className
}: RadarChartProps) {
    // 数据验证
    if (!data || !Array.isArray(data) || data.length === 0) {
        throw new Error("雷达图数据不能为空且必须是数组")
    }

    if (!angleKey || typeof angleKey !== 'string') {
        throw new Error("雷达图需要有效的角度轴字段")
    }

    if (!yKeys || !Array.isArray(yKeys) || yKeys.length === 0) {
        throw new Error("雷达图需要至少一个数值字段")
    }

    // 动态生成chartConfig，添加安全检查
    const chartConfig: ChartConfig = yKeys.reduce((config, key, index) => {
        if (!key || typeof key !== 'string') {
            console.warn(`无效的数值字段: ${key}`)
            return config
        }
        config[key] = {
            label: key.charAt(0).toUpperCase() + key.slice(1),
            color: colors[index % colors.length]
        }
        return config
    }, {} as ChartConfig)

    return (
        <Card className={className}>
            {(title || description) && (
                <CardHeader className="items-center pb-4">
                    {title && <CardTitle>{title}</CardTitle>}
                    {description && <CardDescription>{description}</CardDescription>}
                </CardHeader>
            )}
            <CardContent className="pb-0">
                <ChartContainer
                    config={chartConfig}
                    className="mx-auto aspect-square max-h-[250px]"
                >
                    <RadarChart
                        data={data}
                        margin={{
                            top: 10,
                            right: 10,
                            bottom: 10,
                            left: 10,
                        }}
                    >
                        <ChartTooltip
                            cursor={false}
                            content={<ChartTooltipContent indicator="line" />}
                        />
                        <PolarAngleAxis dataKey={angleKey} />
                        <PolarGrid />
                        {yKeys.map((key, index) => (
                            <Radar
                                key={key}
                                dataKey={key}
                                fill={`var(--color-${key})`}
                                fillOpacity={index === 0 ? 0.6 : 0.3}
                                stroke={`var(--color-${key})`}
                            />
                        ))}
                    </RadarChart>
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