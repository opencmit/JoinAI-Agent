"use client";

import React, { useState } from 'react';
import { Globe, AlertTriangle, CircleDashed, ExternalLink, Search } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import "tdesign-react/es/_util/react-19-adapter";
import { Tooltip, List, Button as TButton } from 'tdesign-react';
import { ChevronRightIcon, ChevronLeftIcon } from 'tdesign-icons-react';

import { AI_NAME } from '@/lib/constants';
import { cn } from "@/lib/utils";

// 动画变体定义
const slideVariants = {
    enterLeft: {
        x: '100%',
        opacity: 0
    },
    enterRight: {
        x: '-100%',
        opacity: 0
    },
    center: {
        x: 0,
        opacity: 1
    },
    exitLeft: {
        x: '-100%',
        opacity: 0
    },
    exitRight: {
        x: '100%',
        opacity: 0
    }
};

interface WebSearchResult {
    url: string;
    title?: string;
    content?: string;
    raw_content?: string;
}

// 定义浏览器操作类型
export interface WebOperation {
    operation?: 'search' | 'scrape';
    query: string;
    status: 'running' | 'finished';
    results: Record<string, any>;
}

interface WebTaskProps {
    operation?: WebOperation | WebOperation[];
}

// 类型检查函数：验证数据是否符合 WebSearchResult 格式
const isWebSearchResult = (data: any): data is WebSearchResult => {
    return data &&
        typeof data === 'object' &&
        typeof data.url === 'string';
};

// 将通用数据转换为 WebSearchResult 格式
const normalizeToWebSearchResult = (data: any): WebSearchResult | null => {
    if (!data || typeof data !== 'object') {
        return null;
    }

    // 如果已经是正确格式，直接返回
    if (isWebSearchResult(data)) {
        return data;
    }

    // 尝试从不同的字段名中提取 URL
    const url = data.url || data.link || data.href || data.address;
    if (!url || typeof url !== 'string') {
        return null;
    }

    // 构造标准化的 WebSearchResult 对象
    return {
        url,
        title: data.title || data.name || data.heading || '无标题',
        content: data.content || data.text || data.description || data.summary,
        raw_content: data.raw_content || data.raw_text || data.body,
    };
};



export const convertRawResults = (rawResults: Record<string, any>) => {
    // 将原始数据转换为 WebSearchResult 格式
    const results: Record<string, WebSearchResult> = {};
    Object.entries(rawResults).forEach(([key, value]) => {
        const normalized = normalizeToWebSearchResult(value);
        if (normalized) {
            results[key] = normalized;
        }
    });
    return results;
}

export const WebTask = React.memo(function WebTask({
    operation
}: WebTaskProps) {
    const [selectedOperation, setSelectedOperation] = useState<WebOperation | null>(null);

    // 获取当前时间
    // const now = new Date();
    // const timeString = now.toLocaleTimeString('zh-CN', {
    //     hour: '2-digit',
    //     minute: '2-digit'
    // });

    const RenderWebTaskDetail = ({ selectedOperation }: { selectedOperation: WebOperation }) => {
        console.log('selectedOperation', selectedOperation);
        const hasResults = Object.keys(selectedOperation.results).length > 0;
        return (
            <div className="flex flex-col h-full w-full justify-self-center bg-transparent">
                {/* 浏览器内容区域 */}
                <div className="w-full rounded-b-lg overflow-y-auto custom-scrollbar px-4 py-4">
                    {selectedOperation.status === 'running' ? (
                        <div className="space-y-4">
                            <div className="flex items-center gap-2 text-gray-600 dark:text-gray-400 justify-center p-6">
                                <CircleDashed className="h-5 w-5 text-blue-500 animate-spin" />
                                <span className="tracking-wide text-sm">
                                    {selectedOperation.operation === 'search' ? '正在搜索网络...' : '正在提取网页内容...'}
                                </span>
                            </div>

                            <div className="space-y-4">
                                {[...Array(2)].map((_, i) => (
                                    <div key={i} className="border border-gray-200 dark:border-gray-600 rounded-lg p-4 animate-pulse">
                                        <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mb-2"></div>
                                        <div className="h-3 bg-zinc-200 dark:bg-zinc-700 rounded w-1/2 mb-3"></div>
                                        <div className="space-y-2">
                                            <div className="h-2 bg-zinc-200 dark:bg-zinc-700 rounded w-full"></div>
                                            <div className="h-2 bg-zinc-200 dark:bg-zinc-700 rounded w-5/6"></div>
                                            <div className="h-2 bg-zinc-200 dark:bg-zinc-700 rounded w-4/5"></div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    ) : (
                        hasResults ? (
                            <div className="space-y-4 w-full max-w-full">
                                {Object.entries(selectedOperation.results).map(([url, result], index) => (
                                    <div key={index} className="bg-white/50 border border-gray-200 dark:border-gray-600 rounded-lg p-4 shadow-sm hover:shadow-md transition-shadow w-full max-w-full box-border">
                                        <div className="flex justify-between items-start mb-2">
                                            <h3 className="font-medium text-blue-600 dark:text-blue-400 mb-1.5 break-words pr-2 text-sm">
                                                {result.title || '无标题'}
                                            </h3>
                                        </div>

                                        <div className="text-xs text-gray-500 dark:text-gray-400 mb-2 flex items-center max-w-full">
                                            <a
                                                href={url}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="text-blue-500 hover:text-blue-600 dark:text-blue-400 dark:hover:text-blue-300 truncate"
                                                title={url}
                                            >
                                                {url}
                                            </a>
                                            <ExternalLink className="h-3 w-3 ml-1 flex-shrink-0" />
                                        </div>

                                        <div className="text-gray-700 dark:text-gray-300 text-sm leading-relaxed overflow-y-auto break-all max-w-full box-border">
                                            {result.content || result.raw_content || '无内容预览'}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="text-center p-8">
                                <AlertTriangle className="h-12 w-12 text-amber-500 mx-auto mb-4" />
                                <p className="text-gray-600 dark:text-gray-400">
                                    {selectedOperation.operation === 'search'
                                        ? '没有找到相关搜索结果'
                                        : '无网页提取内容'}
                                </p>
                            </div>
                        )
                    )}
                </div>
            </div>
        )
    };

    const RenderWebTaskList = ({ operation }: { operation: WebOperation[] }) => {
        return (
            <motion.div
                key="list"
                initial='enterRight'
                animate="center"
                exit='exitLeft'
                variants={slideVariants}
                transition={{ duration: 0.3, ease: 'easeOut' }}
            >
                <List
                    className="h-full bg-linear-122 from-[#EFF3FC] via-[#FDFEFF6B] to-[#F9FAFE19] px-4 py-2"
                    style={{
                        background: 'linear-gradient(122.45deg, #EFF3FC 0%, #FDFEFF6B 44%, #F9FAFE19 100%)',
                        borderRadius: '10px',
                        color: '#363B64',
                        fontFamily: 'PingFang SC',
                        fontWeight: 'regular',
                        fontSize: '14px',
                        lineHeight: '14px',
                        letterSpacing: '0px',
                        textAlign: 'left',
                        overflow: 'hidden',
                    }}
                >
                    {operation.map((op, index) => (
                        <div
                            key={index}
                            className="flex flex-row items-center justify-between p-4 "
                            style={{
                                background: 'linear-gradient(122.45deg, #EFF3FC 0%, #FDFEFF6B 44%, #F9FAFE19 100%)',
                            }}
                        >
                            <div className="max-w-8/10 flex flex-col items-start gap-2">
                                <Tooltip content={op.query} placement="top" showArrow destroyOnClose>
                                    <span className="w-full text-base font-medium truncate">{op.query}</span>
                                </Tooltip>
                                <span className="text-sm">{op.operation === 'search' ? '搜索网络' : '提取网页内容'}</span>
                            </div>
                            <div className='flex items-center gap-2'>
                                {/* 状态指示器 */}
                                <span
                                    className={cn(
                                        'text-xs flex items-center',
                                        op.status === 'finished'
                                            ? 'text-emerald-500 dark:text-emerald-400'
                                            : 'text-rose-500 dark:text-rose-400',
                                    )}
                                >
                                    <span className="h-1.5 w-1.5 rounded-full mr-1.5 bg-current"></span>
                                    {op.status === 'finished' ? '完成' : '搜索中'}
                                </span>
                                <TButton size="large" shape="circle" variant="text" onClick={() => {
                                    setSelectedOperation(op);
                                }}>
                                    <ChevronRightIcon className="h-5 w-5" />
                                </TButton>
                            </div>
                        </div>
                        // <ListItem
                        //     key={index}
                        //     action={
                        //         <div className='flex items-center gap-2'>
                        //             {/* 状态指示器 */}
                        //             <span
                        //                 className={cn(
                        //                     'text-xs flex items-center',
                        //                     op.status === 'finished'
                        //                         ? 'text-emerald-500 dark:text-emerald-400'
                        //                         : 'text-rose-500 dark:text-rose-400',
                        //                 )}
                        //             >
                        //                 <span className="h-1.5 w-1.5 rounded-full mr-1.5 bg-current"></span>
                        //                 {op.status === 'finished' ? '完成' : '搜索中'}
                        //             </span>
                        //             <TButton size="large" shape="circle" variant="text" onClick={() => {
                        //                 setSelectedOperation(op);
                        //             }}>
                        //                 <ChevronRightIcon className="h-5 w-5" />
                        //             </TButton>
                        //         </div>
                        //     }
                        //     style={{
                        //         background: 'linear-gradient(122.45deg, #EFF3FC 0%, #FDFEFF6B 44%, #F9FAFE19 100%)',
                        //     }}
                        // >
                        //     <ListItemMeta className="max-w-8/10 overflow-hidden" title={
                        //         // <Tooltip content={op.query} placement="top" showArrow destroyOnClose>
                        //         //     <span className="max-w-8/10 truncate">{op.query + op.query + op.query}</span>
                        //         // </Tooltip>
                        //         <span className="max-w-9/10 truncate">{op.query + op.query + op.query}</span>
                        //     } description={op.operation === 'search' ? '搜索网络' : '提取网页内容'} />
                        // </ListItem>
                    ))}
                </List>
            </motion.div>
        )
    };

    const RenderWebTaskForDesktop = ({ operation }: { operation: WebOperation }) => {
        const hasResults = Object.keys(operation.results).length > 0;
        return (
            <div className="flex flex-col h-full w-full justify-self-center bg-transparent">
                {/* 浏览器标题栏 */}
                <div className="flex items-center justify-between bg-gray-100 px-4 py-2 rounded-t-lg border-b border-gray-200">
                    <div className="flex items-center space-x-2">
                        <div className="flex space-x-1">
                            <div className="w-3 h-3 bg-red-400 rounded-full"></div>
                            <div className="w-3 h-3 bg-yellow-400 rounded-full"></div>
                            <div className="w-3 h-3 bg-green-400 rounded-full"></div>
                        </div>
                        <Globe className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                            {operation.operation === 'search' ? '网络搜索' : '网页内容提取'}
                        </span>
                    </div>
                    <div className="flex items-center space-x-2">
                        <div className="w-4 h-4 bg-gray-300 dark:bg-gray-600 rounded"></div>
                        <div className="w-4 h-4 bg-gray-300 dark:bg-gray-600 rounded"></div>
                    </div>
                </div>

                {/* 浏览器地址栏 */}
                <div className="flex items-center bg-gray-50 px-4 py-2 border-b border-gray-200">
                    <Search className="w-4 h-4 text-gray-500 mr-2" />
                    <div className="flex-1 bg-white dark:bg-gray-800 rounded px-3 py-1 text-sm text-gray-600 dark:text-gray-400 border border-gray-300 dark:border-gray-600">
                        {operation.query || '正在搜索...'}
                    </div>
                </div>

                {/* 浏览器内容区域 */}
                <div className="w-full rounded-b-lg overflow-y-auto custom-scrollbar bg-white px-4 py-4">
                    {operation.query && hasResults && (
                        <div className="mb-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
                            <div className="flex items-start">
                                <span className="text-blue-600 dark:text-blue-400 shrink-0 mr-2 font-semibold text-sm">
                                    {AI_NAME}@web:
                                </span>
                                <span className="text-gray-700 dark:text-gray-300 text-sm break-words">{operation.query}</span>
                            </div>
                        </div>
                    )}

                    {operation.status === 'running' ? (
                        <div className="space-y-4">
                            <div className="flex items-center gap-2 text-gray-600 dark:text-gray-400 justify-center p-6">
                                <CircleDashed className="h-5 w-5 text-blue-500 animate-spin" />
                                <span className="tracking-wide text-sm">
                                    {operation.operation === 'search' ? '正在搜索网络...' : '正在提取网页内容...'}
                                </span>
                            </div>

                            <div className="space-y-4">
                                {[...Array(2)].map((_, i) => (
                                    <div key={i} className="border border-gray-200 dark:border-gray-600 rounded-lg p-4 animate-pulse">
                                        <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mb-2"></div>
                                        <div className="h-3 bg-zinc-200 dark:bg-zinc-700 rounded w-1/2 mb-3"></div>
                                        <div className="space-y-2">
                                            <div className="h-2 bg-zinc-200 dark:bg-zinc-700 rounded w-full"></div>
                                            <div className="h-2 bg-zinc-200 dark:bg-zinc-700 rounded w-5/6"></div>
                                            <div className="h-2 bg-zinc-200 dark:bg-zinc-700 rounded w-4/5"></div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    ) : (
                        hasResults ? (
                            <div className="space-y-4 w-full max-w-full">
                                {Object.entries(operation.results).map(([url, result], index) => (
                                    <div key={index} className="border border-gray-200 dark:border-gray-600 rounded-lg p-4 shadow-sm hover:shadow-md transition-shadow w-full max-w-full box-border">
                                        <div className="flex justify-between items-start mb-2">
                                            <h3 className="font-medium text-blue-600 dark:text-blue-400 mb-1.5 break-words pr-2 text-sm">
                                                {result.title || '无标题'}
                                            </h3>
                                        </div>

                                        <div className="text-xs text-gray-500 dark:text-gray-400 mb-2 flex items-center max-w-full">
                                            <a
                                                href={url}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="text-blue-500 hover:text-blue-600 dark:text-blue-400 dark:hover:text-blue-300 truncate"
                                                title={url}
                                            >
                                                {url}
                                            </a>
                                            <ExternalLink className="h-3 w-3 ml-1 flex-shrink-0" />
                                        </div>

                                        <div className="text-gray-700 dark:text-gray-300 text-sm leading-relaxed overflow-y-auto break-all max-w-full box-border">
                                            {result.content || result.raw_content || '无内容预览'}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="text-center p-8">
                                <AlertTriangle className="h-12 w-12 text-amber-500 mx-auto mb-4" />
                                <p className="text-gray-600 dark:text-gray-400">
                                    {operation.operation === 'search'
                                        ? '没有找到相关搜索结果'
                                        : '无网页提取内容'}
                                </p>
                            </div>
                        )
                    )}
                </div>
            </div>
        )
    }

    return (
        <>
            {operation instanceof Array ? (
                // 用户点击【浏览器tab】，进入全部浏览器展示状态
                operation.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-32 text-zinc-400 dark:text-zinc-600">
                        <span>暂无浏览器操作</span>
                    </div>
                ) : (
                    <div className="relative h-full overflow-hidden">
                        <AnimatePresence mode="wait">
                            {selectedOperation ? (
                                // 单个浏览器预览展示

                                <motion.div
                                    key="detail"
                                    className='flex flex-col h-full bg-linear-122 from-[#EFF3FC] via-[#FDFEFF6B] to-[#F9FAFE19] rounded-t-lg'
                                    initial='enterLeft'
                                    animate="center"
                                    exit='exitRight'
                                    variants={slideVariants}
                                    transition={{ duration: 0.3, ease: 'easeOut' }}
                                >
                                    <div className="flex items-center justify-between">
                                        <div className="flex items-center">
                                            <TButton size="large" shape="circle" variant="text" onClick={() => {
                                                setSelectedOperation(null);
                                            }}>
                                                <ChevronLeftIcon className="h-4 w-4" />
                                            </TButton>
                                            <span className="text-sm font-medium text-zinc-800 dark:text-zinc-200 w-60 truncate">
                                                {selectedOperation.query}
                                            </span>
                                        </div>

                                        <span
                                            className={cn(
                                                'text-xs flex items-center pr-4',
                                                selectedOperation.status === 'finished'
                                                    ? 'text-emerald-500 dark:text-emerald-400'
                                                    : 'text-rose-500 dark:text-rose-400',
                                            )}
                                        >
                                            <span className="h-1.5 w-1.5 rounded-full mr-1.5 bg-current"></span>
                                            {selectedOperation.status === 'finished' ? '完成' : '搜索中'}
                                        </span>
                                    </div>
                                    <div className="flex-1 bg-transparent overflow-hidden">
                                        <div className="h-full text-zinc-800 dark:text-zinc-200 bg-transparent">
                                            <RenderWebTaskDetail selectedOperation={selectedOperation} />
                                        </div>
                                    </div>
                                </motion.div>
                            ) : (
                                // 浏览器列表展示
                                <RenderWebTaskList operation={operation} />
                            )}
                        </AnimatePresence>
                    </div>
                )
            ) : operation instanceof Object ? (
                // 用户点击【聚智桌面】，单个浏览器的预览展示
                <RenderWebTaskForDesktop operation={operation} />
            ) : (
                <></>
            )}
        </>
    );
});
