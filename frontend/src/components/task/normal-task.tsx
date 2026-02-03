"use client";

import React from 'react';
import { ProcessedMessage } from './task';
import { MarkdownText } from '../assistant-ui/markdown-text';
import { Loader2 } from 'lucide-react';

export interface ImageOperation {
    imageList?: string[]; // Base64编码的图片列表
}

interface NormalTaskProps {
    operation: ProcessedMessage;
}

export default function NormalTask({
    operation,
}: NormalTaskProps) {
    console.log("operation in NormalTask", operation);

    const isJson = (content: string) => {
        try {
            JSON.parse(content);
            return true;
        } catch {
            return false;
        }
    }

    const formatJson = (content: string) => {
        try {
            return '```json\n' + JSON.stringify(JSON.parse(content), null, 2) + '\n```';
        } catch (e) {
            console.warn("Error parsing JSON:", e);
            return content;
        }
    }
    return (
        <div
            className="border-none rounded-xl overflow-y-auto flex flex-col h-full shadow-none"
        >
            {operation.action.toolCalls?.map((op, index) => (
                <div className="flex flex-col h-fit bg-white/40 backdrop-blur-sm rounded-xl" key={index}>
                    <div className="z-50 border-b border-zinc-200/50 dark:border-zinc-700/50">
                        <div className="flex items-center justify-between px-6 py-2">
                            <span className="text-[#363B64] text-base">执行工具 - {op.function.name}</span>
                            {!operation.results || operation.results.length === 0 ? (
                                <div className="flex items-center gap-2 text-blue-500 text-sm">
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                    <span className="">执行中</span>
                                </div>
                            ) : (
                                <span className="text-green-500 text-sm">执行完成</span>
                            )}
                        </div>
                    </div>


                    <div className="flex flex-col gap-2 justify-between px-6 pt-2 pb-4 min-h-0">
                        <div className="flex flex-col gap-2 overflow-hidden">
                            <span className="text-[#363B64] text-base">· 执行参数</span>
                            <MarkdownText className={`max-h-60 flex flex-col custom-scrollbar border border-gray-300/20 ${isJson(op.function.arguments) ? 'rounded-md bg-indigo-100/40' : 'bg-indigo-100/40 py-3 px-4 rounded-md'}`}>{formatJson(op.function.arguments)}</MarkdownText>
                        </div>
                        <div>
                            {operation.results.map((result, index) => {
                                if (result.toolCallId === op.id) {
                                    return (
                                        <div className="flex flex-col gap-2" key={index}>
                                            <span className="text-[#363B64] text-base">· 执行结果</span>
                                            <MarkdownText className={`max-h-60 flex flex-col custom-scrollbar border border-gray-300/20 ${isJson(result.content) ? 'rounded-md bg-indigo-100/40' : 'bg-indigo-100/40 py-3 px-4 rounded-md'}`}>{formatJson(result.content)}</MarkdownText>
                                        </div>
                                    )
                                }
                            })}
                        </div>
                    </div>
                </div>
            ))}
        </div>
    );
}
