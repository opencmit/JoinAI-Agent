"use client";
import React, { useState } from 'react';
import { Globe, CheckCircle, AlertTriangle, ExternalLink, Server, Network, Monitor } from 'lucide-react';
import { cn } from "@/lib/utils";
import { ScrollArea } from "@/components/ui/scroll-area"
import { useSandboxContext } from "@/lib/agent-context";
import { MiniBrowser } from "@/components/mini-browser/mini-browser";
import { Toggle } from "@/components/ui/toggle";

interface ExposePortInfo {
    exposed_url: string;
    description: string;
}

interface ExposePortTaskProps {
    port?: number;
    tool_call_id?: string;
}

// 类型检查函数：验证数据是否符合 ExposePortInfo 格式
const isExposePortInfo = (data: any): data is ExposePortInfo => {
    return data &&
        typeof data === 'object' &&
        typeof data.exposed_url === 'string' &&
        typeof data.description === 'string';
};

// 将通用数据转换为 ExposePortInfo 格式
const normalizeToExposePortInfo = (data: any): ExposePortInfo | null => {
    if (!data || typeof data !== 'object') {
        return null;
    }

    // 如果已经是正确格式，直接返回
    if (isExposePortInfo(data)) {
        return data;
    }

    // 尝试从不同的字段名中提取信息
    const exposed_url = data.exposed_url || data.url || data.link;
    const description = data.description || data.desc || data.message;

    if (!exposed_url || typeof exposed_url !== 'string') {
        return null;
    }

    // 构造标准化的 ExposePortInfo 对象
    return {
        exposed_url,
        description: description || '端口暴露服务',
    };
};

export const ExposePortTask = React.memo(function ExposePortTask({
    port,
    tool_call_id = ''
}: ExposePortTaskProps) {
    // 从 context 获取 agentState
    const { agentState } = useSandboxContext();
    const [showBrowser, setShowBrowser] = useState(false);

    console.log("state in expose port task", agentState);

    const rawResults = agentState.structure_tool_results?.[tool_call_id] || {};

    // 开发调试使用
    // const rawResults = {
    //     "expose_port_info": {
    //         "exposed_url": "http://127.0.0.1:100086",
    //         "description": "沙箱端口 100086 暴露的预览地址"
    //     }
    // }

    // 将原始数据转换为 ExposePortInfo 格式
    let exposePortInfo: ExposePortInfo | null = null;

    // 查找 expose_port_info 字段
    if (rawResults.expose_port_info) {
        exposePortInfo = normalizeToExposePortInfo(rawResults.expose_port_info);
    }

    const hasResult = exposePortInfo !== null;

    return (
        <div className="flex flex-col h-full">
            <div className="flex-1 p-2 overflow-auto">
                <div className="border border-zinc-200/100 dark:border-zinc-800/50 rounded-xl overflow-hidden h-full flex flex-col bg-gradient-to-b from-zinc-50/50 to-zinc-100/30 dark:from-zinc-950/50 dark:to-zinc-900/30 shadow-lg">
                    <div className="flex items-center p-3 bg-gradient-to-r from-zinc-100/80 to-zinc-200/50 dark:from-zinc-900/80 dark:to-zinc-800/50 justify-between border-b border-zinc-200/30 dark:border-zinc-800/30">
                        <div className="flex items-center">
                            <Server className="h-4 w-4 mr-2 text-zinc-600 dark:text-zinc-400" />
                            <span className="text-xs font-medium text-zinc-700 dark:text-zinc-300 tracking-wide">
                                端口暴露服务
                            </span>
                        </div>
                        <div className="flex items-center gap-3">
                            {hasResult && exposePortInfo && (
                                <div className="flex items-center gap-2">
                                    <Toggle
                                        pressed={showBrowser}
                                        onPressedChange={setShowBrowser}
                                        size="sm"
                                        className="h-6 px-2 text-xs data-[state=on]:bg-blue-100"
                                    >
                                        <Monitor className="h-3 w-3 mr-1" />
                                        浏览器
                                    </Toggle>
                                </div>
                            )}
                            <span
                                className={cn(
                                    'text-xs flex items-center',
                                    hasResult
                                        ? 'text-emerald-500 dark:text-emerald-400'
                                        : 'text-rose-500 dark:text-rose-400',
                                )}
                            >
                                <span className="h-1.5 w-1.5 rounded-full mr-1.5 bg-current"></span>
                                {hasResult ? '端口已暴露' : '暴露失败'}
                            </span>
                        </div>
                    </div>

                    <div className="expose-port-container flex-1 overflow-auto bg-gradient-to-b from-zinc-50/95 to-zinc-100/90 dark:from-zinc-900/95 dark:to-zinc-800/90 text-zinc-800 dark:text-zinc-300">
                        {hasResult && exposePortInfo && showBrowser ? (
                            // 浏览器视图 - 填充满整个content区域
                            <div className="h-full">
                                <MiniBrowser
                                    url={exposePortInfo.exposed_url}
                                    disableUrlInput={true}
                                    height="calc(70vh - 10rem)"
                                    className="border-0 shadow-none h-full"
                                />
                            </div>
                        ) : (
                            // 普通工具result视图
                            <div className="p-4">
                                <div className="text-xs space-y-3">
                                    <ScrollArea className="h-[calc(70vh-10rem)]">
                                        {hasResult && exposePortInfo && (
                                            <div className="space-y-4">
                                                <div className="border border-emerald-200 dark:border-emerald-700 rounded-lg p-4 shadow-sm bg-emerald-50/50 dark:bg-emerald-950/30">
                                                    <div className="flex items-center mb-3">
                                                        <CheckCircle className="h-5 w-5 text-emerald-600 dark:text-emerald-400 mr-2" />
                                                        <h3 className="font-medium text-emerald-700 dark:text-emerald-300">
                                                            端口暴露成功
                                                        </h3>
                                                    </div>

                                                    <div className="space-y-3">
                                                        <div>
                                                            <label className="text-xs font-medium text-zinc-600 dark:text-zinc-400 block mb-1">
                                                                暴露的URL:
                                                            </label>
                                                            <div className="flex items-center bg-white dark:bg-zinc-800 rounded-md p-2 border border-zinc-200 dark:border-zinc-700">
                                                                <Network className="h-4 w-4 text-blue-500 mr-2" />
                                                                <a
                                                                    href={exposePortInfo.exposed_url}
                                                                    target="_blank"
                                                                    rel="noopener noreferrer"
                                                                    className="text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300 font-mono text-sm flex-1 truncate"
                                                                >
                                                                    {exposePortInfo.exposed_url}
                                                                </a>
                                                                <ExternalLink className="h-4 w-4 ml-2 text-zinc-500" />
                                                            </div>
                                                        </div>

                                                        <div>
                                                            <label className="text-xs font-medium text-zinc-600 dark:text-zinc-400 block mb-1">
                                                                描述:
                                                            </label>
                                                            <div className="bg-white dark:bg-zinc-800 rounded-md p-2 border border-zinc-200 dark:border-zinc-700">
                                                                <p className="text-sm text-zinc-700 dark:text-zinc-300">
                                                                    {exposePortInfo.description}
                                                                </p>
                                                            </div>
                                                        </div>

                                                        {port && (
                                                            <div>
                                                                <label className="text-xs font-medium text-zinc-600 dark:text-zinc-400 block mb-1">
                                                                    端口号:
                                                                </label>
                                                                <div className="bg-white dark:bg-zinc-800 rounded-md p-2 border border-zinc-200 dark:border-zinc-700">
                                                                    <span className="text-sm font-mono text-zinc-700 dark:text-zinc-300">
                                                                        {port}
                                                                    </span>
                                                                </div>
                                                            </div>
                                                        )}
                                                    </div>

                                                    <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-950/30 rounded-md border border-blue-200 dark:border-blue-800">
                                                        <div className="flex items-start">
                                                            <Globe className="h-4 w-4 text-blue-600 dark:text-blue-400 mr-2 mt-0.5" />
                                                            <div className="text-xs text-blue-700 dark:text-blue-300">
                                                                <p className="font-medium mb-1">访问提示:</p>
                                                                <p>点击上方URL即可访问暴露的服务。确保你的应用程序正在指定端口上运行。</p>
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        )}

                                        {!hasResult && (
                                            <div className="text-center p-6">
                                                <AlertTriangle className="h-8 w-8 text-amber-500 mx-auto mb-2" />
                                                <p className="text-zinc-600 dark:text-zinc-400 mb-2">
                                                    端口暴露失败
                                                </p>
                                                <p className="text-xs text-zinc-500 dark:text-zinc-500">
                                                    请检查端口号是否有效，或者服务是否正在运行
                                                </p>
                                            </div>
                                        )}
                                    </ScrollArea>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
});
