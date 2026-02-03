
import React, { useState, memo } from "react";
import {
    Check,
    Loader2,
    Globe2,
    FileText,
    AlertCircle,
    HelpCircle,
    CheckCircle,
    Sparkles
} from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FilesTask } from "@/components/task/files-task-v2";
import { Chart } from "@/components/chart";

import { getFileContent } from "@/lib/sandbox_manager";

// 独立的MessageToolContent组件，修复React Hook Rules错误
interface MessageToolContentProps {
    status: string;
    args: any;
    sandboxId: string | undefined;
}

export const MessageToolContent = memo<MessageToolContentProps>(function MessageToolContent({ status, args, sandboxId }) {
    const [selectedFile, setSelectedFile] = useState<string | null>(null);
    const [fileContent, setFileContent] = useState<string | null>(null);
    const [loadingFile, setLoadingFile] = useState<string | null>(null);

    // 加载单个文件内容
    const loadFileContent = async (filePath: string) => {
        setLoadingFile(filePath);
        try {
            const content = await getFileContent(sandboxId || "", filePath);
            setFileContent(content as string || "文件为空或读取失败");
        } catch (error) {
            console.error(`读取文件 ${filePath} 失败:`, error);
            setFileContent(`读取文件失败: ${error}`);
        } finally {
            setLoadingFile(null);
        }
    };

    // 处理文件点击
    const handleFileClick = (filePath: string) => {
        if (selectedFile === filePath) {
            // 如果点击的是已选中的文件，则取消选中
            setSelectedFile(null);
            setFileContent(null);
        } else {
            // 选中新文件并加载内容
            setSelectedFile(filePath);
            loadFileContent(filePath);
        }
    };

    // 操作类型映射
    const operationConfig = {
        ask: {
            title: "AI助手提问",
            description: "AI助手需要你的回答来继续执行任务",
            icon: <HelpCircle className="w-5 h-5 text-blue-500" />,
            color: "text-blue-600",
            bgColor: "bg-blue-50",
            borderColor: "border-blue-200"
        },
        web_browser_takeover: {
            title: "浏览器操作请求",
            description: "AI助手需要你手动完成一些浏览器操作",
            icon: <Globe2 className="w-5 h-5 text-orange-500" />,
            color: "text-orange-600",
            bgColor: "bg-orange-50",
            borderColor: "border-orange-200"
        },
        show_chart: {
            title: "图表显示",
            description: "AI助手为你生成了图表",
            icon: <Sparkles className="w-5 h-5 text-purple-500" />,
            color: "text-purple-600",
            bgColor: "bg-purple-50",
            borderColor: "border-purple-200"
        },
        complete: {
            title: "任务完成",
            description: "所有任务已成功完成",
            icon: <CheckCircle className="w-5 h-5 text-green-500" />,
            color: "text-green-600",
            bgColor: "bg-green-50",
            borderColor: "border-green-200"
        }
    };

    const config = operationConfig[args.operation as keyof typeof operationConfig] || operationConfig.ask;

    // 如果是 show_chart 操作，直接渲染 Chart 组件
    if (args.operation === "show_chart" && args.chart_type && args.chart_data) {
        return (
            // 使用一个 div 包裹，并设置最大宽度和居中
            <div className="w-full flex justify-center"> {/* 添加 flex justify-center 来居中内部元素 */}
                <div className="max-w-3xl w-full"> {/* 添加 max-w-2xl 来限制最大宽度，w-full 确保在小于最大宽度时可以填充 */}
                    <Chart
                        type={args.chart_type}
                        data={args.chart_data}
                        title={args.chart_title}
                        description={args.chart_description}
                        {...(args.chart_config || {})}
                        className="w-full h-auto"
                    />
                </div>
            </div>
        );
    }

    // 对于其他操作，使用 Card 组件进行包裹
    return (
        <Card className={`gap-0 my-2 ${config.borderColor} ${config.bgColor} max-w-100`}>
            <CardHeader className="pb-2">
                <div className="flex items-center gap-3">
                    {config.icon}
                    <div className="flex-1">
                        <div className="flex items-center gap-2">
                            <CardTitle className={`text-sm ${config.color}`}>{config.title}</CardTitle>
                            {status === "inProgress" ? (
                                <Loader2 className="w-3 h-3 animate-spin" />
                            ) : (
                                <Check className="w-3 h-3 text-green-500" />
                            )}
                        </div>
                    </div>
                </div>
            </CardHeader>

            <CardContent className="pt-0 space-y-3">
                {/* 显示消息文本 */}
                {args.text && (
                    <div className="bg-white/80 rounded-md p-3 border-blue-200">
                        <p className="text-gray-800 text-sm leading-relaxed">{args.text}</p>
                    </div>
                )}

                {/* 显示附件列表 */}
                {/* 确保 args.attachments 是一个数组再进行 map 操作 */}
                {Array.isArray(args.attachments) && args.attachments.length > 0 && (
                    <div>
                        <div className="flex items-center gap-2 mb-2">
                            <FileText className="w-3 h-3 text-gray-500" />
                            <span className="text-xs font-medium text-gray-600">
                                附件 ({args.attachments.length})
                            </span>
                        </div>
                        <div className="space-y-1">
                            {args.attachments.map((filePath: string, index: number) => (
                                <div key={index}>
                                    <button
                                        onClick={() => handleFileClick(filePath)}
                                        className={`flex items-center gap-2 text-xs p-2 rounded-md hover:bg-white/50 transition-colors w-full text-left border ${selectedFile === filePath
                                            ? 'bg-white/80 text-blue-700 border-blue-200'
                                            : 'text-gray-600 hover:text-gray-800 border-gray-200 bg-white/30'
                                            }`}
                                    >
                                        <FileText className="w-3 h-3 flex-shrink-0" />
                                        <span className="truncate">{filePath.split('/').pop()}</span>
                                        {loadingFile === filePath && (
                                            <Loader2 className="w-3 h-3 animate-spin ml-auto" />
                                        )}
                                    </button>

                                    {/* 显示选中文件的内容 */}
                                    {selectedFile === filePath && fileContent !== null && (
                                        <div className="mt-2 ml-4">
                                            <FilesTask
                                                operation={{
                                                    operation: "read",
                                                    path: filePath,
                                                    content: fileContent,
                                                    isSuccess: true
                                                }}
                                                sandboxId={sandboxId || undefined}
                                            />
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* 根据操作类型显示状态信息 */}
                {args.operation === "ask" && (
                    <div className="flex items-center gap-2 text-xs p-2 rounded-md bg-white/50 border-blue-300 border">
                        <HelpCircle className="w-3 h-3 text-blue-600" />
                        <span className="text-blue-700">请在对话框中回答</span>
                    </div>
                )}

                {args.operation === "web_browser_takeover" && (
                    <div className="flex items-center gap-2 text-xs p-2 rounded-md bg-white/50 border-orange-300 border">
                        <AlertCircle className="w-3 h-3 text-orange-600" />
                        <span className="text-orange-700">请完成操作后在对话框中告知</span>
                    </div>
                )}

                {args.operation === "show_chart" && (
                    <div className="flex items-center gap-2 text-xs p-2 rounded-md bg-white/50 border-purple-300 border">
                        <Sparkles className="w-3 h-3 text-purple-600" />
                        <span className="text-purple-700">图表已生成完成</span>
                    </div>
                )}

                {args.operation === "complete" && (
                    <div className="flex items-center gap-2 text-xs p-2 rounded-md bg-white/50 border-green-300 border">
                        <CheckCircle className="w-3 h-3 text-green-600" />
                        <span className="text-green-700">任务已完成</span>
                    </div>
                )}
            </CardContent>
        </Card>
    );
}, (prevProps, nextProps) => {
    // 自定义比较函数：只有相关的 props 变化时才重新渲染
    // 对于图表操作，我们特别关注是否是图表完成的状态变化
    if (prevProps.args.operation === "show_chart" && nextProps.args.operation === "show_chart") {
        // 对于图表操作，只有在图表数据或类型真正变化时才重新渲染
        return (
            prevProps.status === nextProps.status &&
            prevProps.args.chart_type === nextProps.args.chart_type &&
            prevProps.args.chart_title === nextProps.args.chart_title &&
            prevProps.args.chart_description === nextProps.args.chart_description &&
            JSON.stringify(prevProps.args.chart_data) === JSON.stringify(nextProps.args.chart_data) &&
            JSON.stringify(prevProps.args.chart_config) === JSON.stringify(nextProps.args.chart_config)
        );
    }

    // 对于其他操作，比较基本 props
    return (
        prevProps.status === nextProps.status &&
        prevProps.sandboxId === nextProps.sandboxId &&
        JSON.stringify(prevProps.args) === JSON.stringify(nextProps.args)
    );
});