"use client"

import { TrendingUp } from "lucide-react"
import { CartesianGrid, Line, LineChart, XAxis } from "recharts"
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

interface LineChartProps {
    data: DataPoint[]
    title?: string
    description?: string
    xKey: string
    yKeys: string[]
    colors?: string[]
    showTrend?: boolean
    trendText?: string
    className?: string
}

export const CustomLineChart = memo<LineChartProps>(function CustomLineChart({
    data,
    title,
    description,
    xKey,
    yKeys,
    colors = ["var(--chart-1)", "var(--chart-2)", "var(--chart-3)", "var(--chart-4)", "var(--chart-5)"],
    showTrend = false,
    trendText,
    className
}: LineChartProps) {
    // 数据验证
    if (!data || !Array.isArray(data) || data.length === 0) {
        throw new Error("折线图数据不能为空且必须是数组")
    }

    if (!xKey || typeof xKey !== 'string') {
        throw new Error("折线图需要有效的 X 轴字段")
    }

    if (!yKeys || !Array.isArray(yKeys) || yKeys.length === 0) {
        throw new Error("折线图需要至少一个 Y 轴字段")
    }

    // 动态生成chartConfig，添加安全检查
    const chartConfig: ChartConfig = yKeys.reduce((config, key, index) => {
        if (!key || typeof key !== 'string') {
            console.warn(`无效的 Y 轴字段: ${key}`)
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
                <CardHeader>
                    {title && <CardTitle>{title}</CardTitle>}
                    {description && <CardDescription>{description}</CardDescription>}
                </CardHeader>
            )}
            <CardContent>
                <ChartContainer config={chartConfig}>
                    <LineChart
                        accessibilityLayer
                        data={data}
                        margin={{
                            left: 12,
                            right: 12,
                        }}
                    >
                        <CartesianGrid vertical={false} />
                        <XAxis
                            dataKey={xKey}
                            tickLine={false}
                            axisLine={false}
                            tickMargin={8}
                            tickFormatter={(value) =>
                                typeof value === 'string' && value.length > 3
                                    ? value.slice(0, 3)
                                    : value
                            }
                        />
                        <ChartTooltip
                            cursor={false}
                            content={<ChartTooltipContent />}
                        />
                        {yKeys.map((key) => (
                            <Line
                                key={key}
                                dataKey={key}
                                type="monotone"
                                stroke={`var(--color-${key})`}
                                strokeWidth={2}
                                dot={false}
                            />
                        ))}
                    </LineChart>
                </ChartContainer>
            </CardContent>
            {showTrend && (
                <CardFooter className="flex-col items-start gap-2 text-sm">
                    <div className="flex gap-2 leading-none font-medium">
                        {trendText || "数据趋势"} <TrendingUp className="h-4 w-4" />
                    </div>
                </CardFooter>
            )}
        </Card>
    )
}); 