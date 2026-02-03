"use client";

import { useEffect, useMemo, useState } from "react";
import {
    Search,
} from "lucide-react";
import { AIMessage, ToolCall } from "@noahlocal/copilotkit-shared";
import { useCopilotChatInternal } from "@noahlocal/copilotkit-react-core";

import { AutoScrollDiv } from "@/components/ui/auto-scroll";
import { Typewriter } from "@/components/ui/typewriter";

import { useAgentContext } from "@/lib/agent-context";

// 小电脑搜索过程展示组件
export function ComputerSearchView({ threadId }: { threadId: string }) {
    const {
        messages,
    } = useCopilotChatInternal({ id: threadId });
    const { agentState } = useAgentContext();

    const [show, setShow] = useState(false);

    const [toolCalls, setToolCalls] = useState<ToolCall[]>([]);
    const [currentIndex, setCurrentIndex] = useState(0);

    useEffect(() => {
        const lastMessage = messages[messages.length - 1] as AIMessage | undefined;
        const computerWebMessage = Boolean(
            lastMessage &&
            lastMessage.role === "assistant" &&
            lastMessage.name === "web",
        );

        if (!computerWebMessage) {
            if (show) {
                setShow(false);
            }
            if (toolCalls.length > 0) {
                setToolCalls([]);
            }
            return;
        }

        let hasResults = false;
        const tempToolCalls: ToolCall[] = [];

        for (const toolcall of lastMessage?.toolCalls || []) {
            tempToolCalls.push(toolcall as ToolCall);
            if (agentState.structure_tool_results?.[toolcall.id]) {
                hasResults = true;
                break;
            }
        }

        if (!hasResults) {
            const hasChanged =
                tempToolCalls.length !== toolCalls.length ||
                tempToolCalls.some((call, index) => call.id !== toolCalls[index]?.id);

            if (hasChanged) {
                setToolCalls(tempToolCalls);
            }

            if (!show) {
                setShow(true);
            }
        }
    }, [messages, agentState, show, toolCalls]);

    useEffect(() => {
        if (!toolCalls || toolCalls.length === 0) {
            return;
        }

        setCurrentIndex(0);

        if (toolCalls.length === 1) {
            return;
        }

        const intervalId = window.setInterval(() => {
            setCurrentIndex((prev) => {
                const next = prev + 1;
                return next >= toolCalls.length ? 0 : next;
            });
        }, 3000);

        return () => {
            window.clearInterval(intervalId);
        };
    }, [toolCalls]);

    const effectiveIndex = useMemo(() => {
        return currentIndex >= toolCalls.length ? 0 : currentIndex;
    }, [currentIndex, toolCalls]);
    const toolCall = useMemo(() => {
        console.log("effectiveIndex", toolCalls, effectiveIndex);
        return toolCalls[effectiveIndex] as ToolCall;
    }, [effectiveIndex, toolCalls]);

    const args = useMemo(() => {
        console.log("toolCall", toolCall);
        const args_string = toolCall?.function.arguments || "{}";
        try {
            return JSON.parse(args_string);
        } catch (error) {
            console.error("Failed to parse tool call arguments", error);
            return {};
        }
    }, [toolCall]);

    const displayQuery = useMemo(() => {
        return args?.sub_queries?.[0]?.query ?? "";
    }, [args]);

    return (
        toolCalls.length > 0 ? (
            <div className="h-68 w-full max-w-180 flex-none w-full px-10 my-3">
                <div className="h-full w-full flex p-6 bg-blue-300 rounded-2xl relative overflow-hidden">
                    <div className="flex-1 flex flex-col rounded-lg animate-slideInFromRight">
                        {/* 浏览器地址栏 */}
                        <div className="flex items-center bg-gray-50 px-4 py-1 border-b border-gray-200 rounded-t-lg">
                            <Search className="w-4 h-4 text-gray-500 mr-2" />
                            <div className="flex-1 bg-white dark:bg-gray-800 rounded px-3 py-1 text-sm text-gray-600 dark:text-gray-400 border border-gray-300 dark:border-gray-600">
                                {/* {(visibleMessages[visibleMessages.length - 1] as ActionExecutionMessage).arguments.title} */}
                                {displayQuery}
                            </div>
                        </div>
                        {/* 浏览器内容区域 */}
                        <div className="flex-1 overflow-hidden bg-white rounded-b-lg">
                            <div className="h-full w-full relative overflow-y-hidden py-2 px-5">
                                <div className="z-10 absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-80 px-4 py-2 rounded-lg shadow-lg bg-white">
                                    <AutoScrollDiv className="flex flex-col max-h-[4.5rem] overflow-y-auto no-scrollbar">
                                        <Typewriter
                                            // text={(visibleMessages[visibleMessages.length - 1] as ActionExecutionMessage).arguments.action}
                                            text={displayQuery}
                                            speed={80}
                                        />
                                    </AutoScrollDiv>
                                </div>
                                <div className="space-y-4 overflow-hidden h-96">
                                    <div className="animate-scroll-up">
                                        {/* 第一组骨架屏 */}
                                        {[...Array(6)].map((_, i) => {
                                            const widths = ['w-3/4', 'w-2/3', 'w-4/5', 'w-1/2', 'w-5/6', 'w-3/5'];
                                            const lineWidths = ['w-full', 'w-5/6', 'w-4/5', 'w-3/4', 'w-2/3', 'w-1/2'];
                                            return (
                                                <div key={`first-${i}`} className="border border-gray-100 dark:border-gray-600 rounded-lg p-4 animate-pulse mb-4">
                                                    <div className={`h-4 bg-gray-200 dark:bg-gray-700 rounded ${widths[i % widths.length]} mb-2`}></div>
                                                    <div className={`h-3 bg-zinc-200 dark:bg-zinc-700 rounded ${widths[(i + 1) % widths.length]} mb-3`}></div>
                                                    <div className="space-y-2">
                                                        <div className={`h-2 bg-zinc-200 dark:bg-zinc-700 rounded ${lineWidths[i % lineWidths.length]}`}></div>
                                                        <div className={`h-2 bg-zinc-200 dark:bg-zinc-700 rounded ${lineWidths[(i + 1) % lineWidths.length]}`}></div>
                                                        <div className={`h-2 bg-zinc-200 dark:bg-zinc-700 rounded ${lineWidths[(i + 2) % lineWidths.length]}`}></div>
                                                    </div>
                                                    <div className="flex justify-between items-center mt-3">
                                                        <div className="h-2 bg-zinc-200 dark:bg-zinc-700 rounded w-1/3"></div>
                                                        <div className="h-2 bg-zinc-200 dark:bg-zinc-700 rounded w-1/4"></div>
                                                    </div>
                                                </div>
                                            );
                                        })}
                                        {/* 第二组骨架屏（重复内容，实现无缝循环） */}
                                        {[...Array(6)].map((_, i) => {
                                            const widths = ['w-3/4', 'w-2/3', 'w-4/5', 'w-1/2', 'w-5/6', 'w-3/5'];
                                            const lineWidths = ['w-full', 'w-5/6', 'w-4/5', 'w-3/4', 'w-2/3', 'w-1/2'];
                                            return (
                                                <div key={`second-${i}`} className="border border-gray-100 dark:border-gray-600 rounded-lg p-4 animate-pulse mb-4">
                                                    <div className={`h-4 bg-gray-200 dark:bg-gray-700 rounded ${widths[i % widths.length]} mb-2`}></div>
                                                    <div className={`h-3 bg-zinc-200 dark:bg-zinc-700 rounded ${widths[(i + 1) % widths.length]} mb-3`}></div>
                                                    <div className="space-y-2">
                                                        <div className={`h-2 bg-zinc-200 dark:bg-zinc-700 rounded ${lineWidths[i % lineWidths.length]}`}></div>
                                                        <div className={`h-2 bg-zinc-200 dark:bg-zinc-700 rounded ${lineWidths[(i + 1) % lineWidths.length]}`}></div>
                                                        <div className={`h-2 bg-zinc-200 dark:bg-zinc-700 rounded ${lineWidths[(i + 2) % lineWidths.length]}`}></div>
                                                    </div>
                                                    <div className="flex justify-between items-center mt-3">
                                                        <div className="h-2 bg-zinc-200 dark:bg-zinc-700 rounded w-1/3"></div>
                                                        <div className="h-2 bg-zinc-200 dark:bg-zinc-700 rounded w-1/4"></div>
                                                    </div>
                                                </div>
                                            );
                                        })}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        ) : (
            <></>
        )
    );
}
