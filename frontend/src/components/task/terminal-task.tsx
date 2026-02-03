"use client";

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Terminal, CircleDashed } from 'lucide-react';
import "tdesign-react/es/_util/react-19-adapter";
import { Tooltip, List, Button as TButton } from 'tdesign-react';
import { ChevronRightIcon, ChevronLeftIcon } from 'tdesign-icons-react';

import { ScrollArea } from "@/components/ui/scroll-area"

import { cn } from "@/lib/utils";

const { ListItem, ListItemMeta } = List;

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

// 定义终端操作类型
export interface TerminalOperation {
    command?: string;
    output?: string;
    exitCode?: number;
    isLoading?: boolean;
    workingDirectory?: string;
}

interface TerminalTaskProps {
    // command?: string;
    // output?: string;
    // exitCode?: number;
    // workingDirectory?: string;
    operation?: TerminalOperation | TerminalOperation[];
}

export const TerminalTask = React.memo(function TerminalTask({
    operation
}: TerminalTaskProps) {
    const [selectedOperation, setSelectedOperation] = useState<TerminalOperation | null>(null);

    return (
        <>
            {
                operation instanceof Array ? (
                    // 用户点击【终端tab】，进入全部终端展示状态
                    operation.length === 0 ? (
                        <div className="flex flex-col items-center justify-center h-32 text-zinc-400 dark:text-zinc-600">
                            <span>暂无终端操作</span>
                        </div>
                    ) : (
                        <div className="relative h-full overflow-hidden">
                            <AnimatePresence mode="wait">
                                {selectedOperation ? (
                                    // 单个终端预览展示
                                    <motion.div
                                        key="detail"
                                        className='flex flex-col h-full bg-linear-122 from-[#EFF3FC] via-[#FDFEFF6B] to-[#F9FAFE19] rounded-t-lg'
                                        initial='enterLeft'
                                        animate="center"
                                        exit='exitRight'
                                        variants={slideVariants}
                                        transition={{ duration: 0.3, ease: 'easeOut' }}
                                    >
                                        <div className="flex items-center justify-between px-4">
                                            <div className="flex items-center py-2">
                                                <TButton size="large" shape="circle" variant="text" onClick={() => {
                                                    setSelectedOperation(null);
                                                }}>
                                                    <ChevronLeftIcon className="h-5 w-5" />
                                                </TButton>
                                                <span className="text-sm font-medium text-zinc-800 dark:text-zinc-200 w-60 truncate">
                                                    {selectedOperation.command}
                                                </span>
                                            </div>

                                            <span
                                                className={cn(
                                                    'text-xs flex items-center',
                                                    selectedOperation.exitCode === 0
                                                        ? 'text-emerald-500 dark:text-emerald-400'
                                                        : 'text-rose-500 dark:text-rose-400',
                                                )}
                                            >
                                                <span className="h-1.5 w-1.5 rounded-full mr-1.5 bg-current"></span>
                                                Exit: {selectedOperation.exitCode}
                                            </span>
                                        </div>
                                        <div className="flex-1 bg-transparent overflow-y-auto ">
                                            <div className="h-full text-zinc-800 dark:text-zinc-200 bg-transparent space-y-3">
                                                <div className="flex-1 p-2 overflow-auto">
                                                    <div className="border border-zinc-200/50 dark:border-zinc-800/50 rounded-xl overflow-hidden h-full flex flex-col bg-gradient-to-b from-zinc-50/50 to-zinc-100/30 dark:from-zinc-950/50 dark:to-zinc-900/30">
                                                        <div className="terminal-container flex-1 overflow-auto bg-gradient-to-b from-black/95 to-zinc-900/90 text-zinc-300 font-mono p-4">
                                                            <div className="text-xs space-y-3">
                                                                <ScrollArea className="h-[calc(70vh-10rem)]">
                                                                    {selectedOperation.command && selectedOperation.output && (
                                                                        <div className="space-y-3">
                                                                            <div className="flex items-start">
                                                                                <span className="text-emerald-400 shrink-0 mr-2">
                                                                                    {selectedOperation.workingDirectory}
                                                                                </span>
                                                                                <span className="text-zinc-300 font-medium">{selectedOperation.command}</span>
                                                                            </div>

                                                                            {selectedOperation.output && (
                                                                                <div className="whitespace-pre-wrap break-words text-zinc-400/90 pl-0 leading-relaxed">
                                                                                    {selectedOperation.output}
                                                                                </div>
                                                                            )}

                                                                            {selectedOperation.exitCode === 0 && (
                                                                                <div className="text-emerald-400 mt-2">
                                                                                    {selectedOperation.workingDirectory} _
                                                                                </div>
                                                                            )}
                                                                        </div>
                                                                    )}

                                                                    {!selectedOperation.command && selectedOperation.output && (
                                                                        <div className="flex items-start">
                                                                            <span className="text-emerald-400 shrink-0 mr-2">
                                                                                {selectedOperation.workingDirectory}
                                                                            </span>
                                                                            <span className="w-2 h-4 bg-zinc-500/80 rounded-sm"></span>
                                                                        </div>
                                                                    )}

                                                                    {!selectedOperation.output && (
                                                                        <div className="space-y-3">
                                                                            <div className="flex items-start">
                                                                                <span className="text-emerald-400 shrink-0 mr-2">
                                                                                    {selectedOperation.workingDirectory}
                                                                                </span>
                                                                                <span className="text-zinc-300 font-medium">
                                                                                    {selectedOperation.command || '正在执行命令...'}
                                                                                </span>
                                                                            </div>
                                                                            <div className="flex items-center gap-2 text-zinc-400/80">
                                                                                <CircleDashed className="h-3 w-3 text-blue-400 animate-spin" />
                                                                                <span className="tracking-wide">命令执行中...</span>
                                                                            </div>
                                                                        </div>
                                                                    )}
                                                                </ScrollArea>
                                                            </div>
                                                        </div>
                                                    </div >
                                                </div >
                                            </div>
                                        </div>
                                    </motion.div>
                                ) : (
                                    // 终端列表展示
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
                                                <ListItem
                                                    key={index}
                                                    action={
                                                        <div className='flex items-center gap-2'>
                                                            {/* 状态指示器 */}
                                                            <span
                                                                className={cn(
                                                                    'text-xs flex items-center',
                                                                    op.exitCode === 0
                                                                        ? 'text-emerald-500 dark:text-emerald-400'
                                                                        : 'text-rose-500 dark:text-rose-400',
                                                                )}
                                                            >
                                                                <span className="h-1.5 w-1.5 rounded-full mr-1.5 bg-current"></span>
                                                                {op.exitCode === 0 ? '成功' : '失败'}
                                                            </span>
                                                            <TButton size="large" shape="circle" variant="text" onClick={() => {
                                                                setSelectedOperation(op);
                                                            }}>
                                                                <ChevronRightIcon className="h-5 w-5" />
                                                            </TButton>
                                                        </div>
                                                    }
                                                    style={{
                                                        background: 'linear-gradient(122.45deg, #EFF3FC 0%, #FDFEFF6B 44%, #F9FAFE19 100%)',
                                                    }}
                                                >
                                                    <ListItemMeta title={
                                                        <Tooltip content={op.command} placement="top" showArrow destroyOnClose>
                                                            <div className='flex items-center'>
                                                                <span className="max-w-60 truncate">{op.command}</span>
                                                            </div>
                                                        </Tooltip>
                                                    } />
                                                </ListItem>
                                            ))}
                                        </List>
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </div>
                    )
                ) : operation instanceof Object ? (
                    // 用户点击【聚智桌面】，单个终端的预览展示
                    <div className="flex flex-col h-full">
                        <div className="flex-1 p-2 overflow-auto">
                            <div className="border border-zinc-200/50 dark:border-zinc-800/50 rounded-xl overflow-hidden h-full flex flex-col bg-gradient-to-b from-zinc-50/50 to-zinc-100/30 dark:from-zinc-950/50 dark:to-zinc-900/30">
                                <div className="flex items-center p-3 bg-gradient-to-r from-zinc-100/80 to-zinc-200/50 dark:from-zinc-900/80 dark:to-zinc-800/50 justify-between border-b border-zinc-200/30 dark:border-zinc-800/30">
                                    <div className="flex items-center">
                                        <Terminal className="h-4 w-4 mr-2 text-zinc-600 dark:text-zinc-400" />
                                        <span className="text-xs font-medium text-zinc-700 dark:text-zinc-300 tracking-wide">
                                            终端
                                        </span>
                                    </div >
                                    {operation.exitCode !== null && operation.output && (
                                        <span
                                            className={cn(
                                                'text-xs flex items-center',
                                                operation.exitCode === 0
                                                    ? 'text-emerald-500 dark:text-emerald-400'
                                                    : 'text-rose-500 dark:text-rose-400',
                                            )}
                                        >
                                            <span className="h-1.5 w-1.5 rounded-full mr-1.5 bg-current"></span>
                                            Exit: {operation.exitCode}
                                        </span>
                                    )
                                    }
                                </div >

                                <div className="terminal-container flex-1 overflow-auto bg-gradient-to-b from-black/95 to-zinc-900/90 text-zinc-300 font-mono p-4">
                                    <div className="text-xs space-y-3">
                                        <ScrollArea className="h-[calc(70vh-10rem)]">
                                            {operation.command && operation.output && (
                                                <div className="space-y-3">
                                                    <div className="flex items-start">
                                                        <span className="text-emerald-400 shrink-0 mr-2">
                                                            {operation.workingDirectory}
                                                        </span>
                                                        <span className="text-zinc-300 font-medium">{operation.command}</span>
                                                    </div>

                                                    {operation.output && (
                                                        <div className="whitespace-pre-wrap break-words text-zinc-400/90 pl-0 leading-relaxed">
                                                            {operation.output}
                                                        </div>
                                                    )}

                                                    {operation.exitCode === 0 && (
                                                        <div className="text-emerald-400 mt-2">
                                                            {operation.workingDirectory} _
                                                        </div>
                                                    )}
                                                </div>
                                            )}

                                            {!operation.command && operation.output && (
                                                <div className="flex items-start">
                                                    <span className="text-emerald-400 shrink-0 mr-2">
                                                        {operation.workingDirectory}
                                                    </span>
                                                    <span className="w-2 h-4 bg-zinc-500/80 rounded-sm"></span>
                                                </div>
                                            )}

                                            {!operation.output && (
                                                <div className="space-y-3">
                                                    <div className="flex items-start">
                                                        <span className="text-emerald-400 shrink-0 mr-2">
                                                            {operation.workingDirectory}
                                                        </span>
                                                        <span className="text-zinc-300 font-medium">
                                                            {operation.command || '正在执行命令...'}
                                                        </span>
                                                    </div>
                                                    <div className="flex items-center gap-2 text-zinc-400/80">
                                                        <CircleDashed className="h-3 w-3 text-blue-400" />
                                                        <span className="tracking-wide">命令执行中...</span>
                                                    </div>
                                                </div>
                                            )}
                                        </ScrollArea>
                                    </div>
                                </div>
                            </div >
                        </div >

                        {/* 状态栏 */}
                        {/* <div className="p-2 border-t border-zinc-200 dark:border-zinc-800">
                <div className="flex items-center justify-between text-xs text-zinc-500 dark:text-zinc-400">
                    {!isLoading && (
                        <div className="flex items-center gap-2">
                            {operation.exitCode === 0 ? (
                                <CheckCircle className="h-3.5 w-3.5 text-emerald-500" />
                            ) : (
                                <AlertTriangle className="h-3.5 w-3.5 text-red-500" />
                            )}
                            <span>
                                {operation.exitCode === 0
                                    ? `命令执行成功${exitCode !== null ? ` (退出码: ${exitCode})` : ''}`
                                    : `命令执行失败${exitCode !== null ? ` 退出码 ${exitCode}` : ''}`}
                            </span>
                        </div>
                    )}

                    {isLoading && (
                        <div className="flex items-center gap-2">
                            <CircleDashed className="h-3.5 w-3.5 text-blue-500 animate-spin" />
                            <span>正在执行命令...</span>
                        </div>
                    )}

                    <div className="text-xs">
                        {workingDirectory}
                    </div>
                </div>
            </div> */}
                    </div >
                ) : (
                    <></>
                )
            }
        </>
    )
});
