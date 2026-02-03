"use client"

import React from 'react'
import { AlertCircle, RefreshCw } from 'lucide-react'

interface ChartErrorBoundaryState {
    hasError: boolean
    error: Error | null
    errorInfo: React.ErrorInfo | null
}

interface ChartErrorBoundaryProps {
    children: React.ReactNode
    fallback?: React.ComponentType<ChartErrorFallbackProps>
    onError?: (error: Error, errorInfo: React.ErrorInfo) => void
}

interface ChartErrorFallbackProps {
    error: Error | null
    resetError: () => void
    title?: string
    className?: string
}

/**
 * 默认的图表错误回退组件
 */
function DefaultChartErrorFallback({
    error,
    resetError,
    title,
    className
}: ChartErrorFallbackProps) {
    return (
        <div className={`flex flex-col items-center justify-center p-6 border border-red-300 bg-red-50 rounded-md ${className || ''}`}>
            <AlertCircle className="w-8 h-8 text-red-500 mb-3" />
            <h3 className="text-lg font-medium text-red-700 mb-2">图表渲染失败</h3>
            {title && (
                <p className="text-sm text-red-600 mb-2">图表: {title}</p>
            )}
            <p className="text-sm text-red-600 text-center mb-4">
                {error?.message || '渲染过程中发生未知错误'}
            </p>
            <button
                onClick={resetError}
                className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
            >
                <RefreshCw className="w-4 h-4" />
                重试
            </button>
            {process.env.NODE_ENV === 'development' && error && (
                <details className="mt-4 max-w-full">
                    <summary className="text-xs text-red-500 cursor-pointer">
                        查看详细错误信息 (开发模式)
                    </summary>
                    <pre className="mt-2 text-xs text-red-600 bg-red-100 p-2 rounded overflow-auto max-h-32">
                        {error.stack}
                    </pre>
                </details>
            )}
        </div>
    )
}

/**
 * 图表错误边界组件
 * 
 * 用于捕获图表组件渲染时的任何错误，防止整个应用崩溃
 * 
 * @example
 * <ChartErrorBoundary>
 *   <Chart type="bar" data={chartData} />
 * </ChartErrorBoundary>
 */
export class ChartErrorBoundary extends React.Component<
    ChartErrorBoundaryProps,
    ChartErrorBoundaryState
> {
    constructor(props: ChartErrorBoundaryProps) {
        super(props)
        this.state = {
            hasError: false,
            error: null,
            errorInfo: null
        }
    }

    static getDerivedStateFromError(error: Error): Partial<ChartErrorBoundaryState> {
        // 更新 state 使下一次渲染能够显示降级后的 UI
        return {
            hasError: true,
            error
        }
    }

    componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
        // 记录错误信息
        console.error('Chart Error Boundary caught an error:', error, errorInfo)

        this.setState({
            error,
            errorInfo
        })

        // 调用自定义错误处理函数
        if (this.props.onError) {
            this.props.onError(error, errorInfo)
        }
    }

    resetError = () => {
        this.setState({
            hasError: false,
            error: null,
            errorInfo: null
        })
    }

    render() {
        if (this.state.hasError) {
            const FallbackComponent = this.props.fallback || DefaultChartErrorFallback

            return (
                <FallbackComponent
                    error={this.state.error}
                    resetError={this.resetError}
                />
            )
        }

        return this.props.children
    }
}

/**
 * 高阶组件：为图表组件包装错误边界
 */
export function withChartErrorBoundary<P extends object>(
    WrappedComponent: React.ComponentType<P>,
    errorBoundaryProps?: Omit<ChartErrorBoundaryProps, 'children'>
) {
    const WithErrorBoundaryComponent = (props: P) => (
        <ChartErrorBoundary {...errorBoundaryProps}>
            <WrappedComponent {...props} />
        </ChartErrorBoundary>
    )

    WithErrorBoundaryComponent.displayName = `withChartErrorBoundary(${WrappedComponent.displayName || WrappedComponent.name})`

    return WithErrorBoundaryComponent
}

export default ChartErrorBoundary
export type { ChartErrorFallbackProps } 