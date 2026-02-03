"use client";
import * as React from "react"
import { useEffect, useState, useMemo } from "react";
import Image from 'next/image'
import { useCopilotChatInternal } from "@noahlocal/copilotkit-react-core";
import { Message, AIMessage, ToolResult } from "@noahlocal/copilotkit-shared";
import { Button } from 'tdesign-react';
import { PreviousFilledIcon, NextFilledIcon } from 'tdesign-icons-react';

import {
    Card,
    CardContent,
    CardFooter,
    CardHeader,
    CardTitle,
} from "@/components/ui/card"
import {
    Tabs,
    TabsContent,
    TabsList,
    TabsTrigger,
} from "@/components/ui/tabs"

import { Slider } from "@/components/ui/slider"
import { TerminalTask, TerminalOperation } from "./terminal-task"
import { FilesTask, FileOperation } from "./files-task-v2"
import { WebTask, WebOperation, convertRawResults } from "./web-task";
import { useSandboxContext } from "@/lib/agent-context";
import { showWebMessage } from "@/utils/message";
import { BrowserUseTask } from "./browser-use-task";

// 可以放在文件顶部或者一个独立的工具函数文件中
// const truncateString = (str: string, maxLength: number): string => {
//     if (str && str.length > maxLength) {
//         return str.slice(0, maxLength) + '...';
//     }
//     return str;
// };

export interface ProcessedMessage {
    action: AIMessage;
    results: ToolResult[];
    webResults: Record<string, any>;
}

export function Task({ className, threadId }: { className: string, threadId: string }) {
    const [manualSliderValue, setManualSliderValue] = useState<number | null>(null);
    const [tabValue, setTabValue] = useState<string>("desktop");
    // 使用SandboxContext获取sandboxId
    const { sandboxId, agentState } = useSandboxContext();
    const [processedMessages, setProcessedMessages] = useState<ProcessedMessage[]>([]);

    const {
        messages
    } = useCopilotChatInternal({ id: threadId });

    useEffect(() => {
        const toolCallMessages: AIMessage[] = messages
            .filter((message: Message) => {
                if (message.role === 'assistant' && message.toolCalls) {
                    if (message.name === 'files' || message.name === 'execute_command' || message.name === 'web' || message.name === 'image') {
                        return true;
                    }
                    return false;
                }
                return false;
            }) as AIMessage[]
        // console.log("toolCallMessages", toolCallMessages);

        const toolResultMessages: ToolResult[] = messages
            .filter((message: Message) => {
                if (message.role === 'tool') {
                    return true;
                }
                return false;
            }) as ToolResult[]

        // console.log("toolResultMessages", toolResultMessages);

        const tempMessages: ProcessedMessage[] = []

        for (const toolCallMesssage of toolCallMessages) {
            const toolResultMessage: ToolResult[] = []
            let webResults: Record<string, any> = {}
            for (const toolCall of toolCallMesssage.toolCalls || []) {
                // 如果是web tool，则直接添加结构化工具结果
                if (toolCall.function.name === 'web') {
                    if (showWebMessage(toolCallMesssage, agentState.structure_tool_results || {})) {
                        webResults = agentState.structure_tool_results[toolCall.id] || {}
                    }
                }
                // 如果是其他tool，则添加tool结果
                if (toolResultMessages) {
                    const tempToolResultMessage = toolResultMessages.find((resultMessage: ToolResult) => resultMessage.toolCallId === toolCall.id);
                    if (tempToolResultMessage) {
                        toolResultMessage.push(tempToolResultMessage as ToolResult)
                    }
                }
            }
            // console.log("toolResultMessage in Task", toolResultMessage);
            if (toolCallMesssage.name === 'web') {
                if (Object.keys(webResults).length > 0) {
                    tempMessages.push({
                        action: toolCallMesssage,
                        results: toolResultMessage,
                        webResults: webResults,
                    });
                }
            } else {
                tempMessages.push({
                    action: toolCallMesssage,
                    results: toolResultMessage,
                    webResults: {}
                });
            }
        }

        if (JSON.stringify(tempMessages) !== JSON.stringify(processedMessages)) {
            console.log("tempMessages in Task. tempMessages有变化，更新processedMessages", tempMessages);
            setProcessedMessages(tempMessages);
        }
    }, [messages, agentState.structure_tool_results])

    // 当有browser_use_steps内容时，自动切换到browser_use_steps tab
    useEffect(() => {
        if (agentState.browser_use_steps && Object.keys(agentState.browser_use_steps).length > 0) {
            setTabValue("browser_use_steps");
        }
    }, [agentState.browser_use_steps]);

    // 使用useMemo计算实际的sliderValue
    // 如果用户手动操作过slider，使用手动值；否则自动跟随最新消息
    const sliderValue = useMemo(() => {
        if (!processedMessages || processedMessages.length === 0) {
            return 0;
        }

        // 如果有手动设置的值且在有效范围内，使用手动值
        if (manualSliderValue !== null &&
            manualSliderValue >= 0 &&
            manualSliderValue < processedMessages.length) {
            return manualSliderValue;
        }

        // 否则自动跟随最新消息
        return processedMessages.length - 1;
    }, [processedMessages, manualSliderValue]);

    const handleIncrement = () => {
        setManualSliderValue(prev => {
            const current = prev !== null ? prev : sliderValue;
            return Math.min(processedMessages.length - 1, current + 1);
        });
    };

    const handleDecrement = () => {
        setManualSliderValue(prev => {
            const current = prev !== null ? prev : sliderValue;
            return Math.max(0, current - 1);
        });
    };

    // 判断是否为终端操作
    const isTerminalAction = (actionName: string): boolean => {
        const terminalActions = [
            'execute_command'
        ];
        return terminalActions.some(action => actionName.toLowerCase().includes(action.toLowerCase()));
    };

    // 判断是否为expose_port tool
    // const isExposePortTool = (actionName: string): boolean => {
    //     const exposePortTools = [
    //         'expose_port'
    //     ];
    //     return exposePortTools.some(action => actionName.toLowerCase().includes(action.toLowerCase()));
    // };
    // 判断是否为文件操作
    const isFileAction = (actionName: string): boolean => {
        const fileActions = [
            'files'
        ];
        return fileActions.some(action => actionName.toLowerCase().includes(action.toLowerCase()));
    };

    // 判断是否为message tool
    // const isMessageTool = (actionName: string): boolean => {
    //     const messageTools = [
    //         'message'
    //     ];
    //     return messageTools.some(action => actionName.toLowerCase().includes(action.toLowerCase()));
    // };

    // 判断是否为browser tool
    // const isBrowserTool = (actionName: string): boolean => {
    //     const browserTools = [
    //         'browser'
    //     ];
    //     return browserTools.some(action => actionName.toLowerCase().includes(action.toLowerCase()));
    // };

    // 判断是否为web_search tool
    const isWebSearchTool = (actionName: string): boolean => {
        const webSearchTools = [
            'web'
        ];
        return webSearchTools.some(action => actionName.toLowerCase().includes(action.toLowerCase()));
    };

    // 从action消息中提取FileOperation属性
    const getFileOperation = (message: ProcessedMessage): FileOperation | undefined => {
        // console.log("getFileOperation message", message);
        if (!message.action || !message.action.name || message.action.name !== "files") {
            return undefined;
        }

        // 提取操作相关信息
        try {
            // ActionExecutionMessage包含name和arguments属性
            const args_string = message.action.toolCalls![0].function.arguments || '';
            const args = JSON.parse(args_string);

            return {
                operation: args.operation || 'unknown',
                path: args.path || args.target_file || args.file_path,
                content: args.content,
                old_str: args.old_str,
                new_str: args.new_str,
                files: args.files,
                fileName: args.name || args.path,
                filePath: args.path,
                // path: "测试文件.pptx",
                // fileName: "测试文件.pptx",
                // filePath: "测试文件.pptx",
                fileDate: args.date,
                isLoading: false,
                isSuccess: true,
            };
        } catch (e) {
            console.error("Error parsing action payload:", e);
            return undefined;
        }
    };

    const getAllFileOperation = (processedMessages: ProcessedMessage[]): FileOperation[] | undefined => {

        const fileOperations: FileOperation[] = [];

        for (const message of processedMessages) {
            const fileOperation = getFileOperation(message);
            if (fileOperation) {
                fileOperations.push(fileOperation);
            }
        }

        // console.log("getAllFileOperation", fileOperations);
        return fileOperations;
    }

    // 从action消息中提取TerminalOperation属性
    const getTerminalOperation = (message: ProcessedMessage): TerminalOperation | undefined => {
        if (!message.action || !message.action.name || message.action.name !== "execute_command") {
            return undefined;
        }

        // 提取操作相关信息
        try {
            // ActionExecutionMessage包含name和arguments属性
            console.log("message in getTerminalOperation", message);
            const args_string = message.action.toolCalls?.[0].function.arguments || '';
            const args = JSON.parse(args_string);
            const result = message.results && message.results.length > 0 ? message.results[0].content : undefined;

            return {
                command: args.command || args.cmd || args.script,
                output: result,
                isLoading: false,
                workingDirectory: args.workingDirectory || args.cwd || "/workspace"
            };
        } catch (e) {
            console.error("Error parsing action arguments:", e);
            return undefined;
        }
    };


    const getAllTerminalOperation = (processedMessages: ProcessedMessage[]): TerminalOperation[] | undefined => {

        const terminalOperations: TerminalOperation[] = [];

        for (const message of processedMessages) {
            const terminalOperation = getTerminalOperation(message);
            if (terminalOperation) {
                terminalOperations.push(terminalOperation);
            }
        }

        // console.log("getAllFileOperation", fileOperations);
        return terminalOperations;
    }

    // 从action消息中提取WebOperation属性
    const getWebOperation = (message: ProcessedMessage): WebOperation | undefined => {
        if (!message.action || !message.action.name || message.action.name !== "web") {
            return undefined;
        }

        if (Object.keys(message.action.toolCalls?.[0].function.arguments || {}).length === 0) {
            return undefined;
        }

        console.log("message in getWebOperation", message);

        const args_string = message.action.toolCalls?.[0].function.arguments || '';
        const args = JSON.parse(args_string);

        return {
            operation: args.operation,
            query: args.query || args.sub_queries?.[0]?.query || args.urls?.[0] || "网络搜索",
            status: 'finished',
            results: convertRawResults(message.webResults || {}),
        };
    };

    const getAllWebOperation = (processedMessages: ProcessedMessage[]): WebOperation[] | undefined => {

        const webOperations: WebOperation[] = [];

        for (const message of processedMessages) {
            const webOperation = getWebOperation(message);
            if (webOperation) {
                webOperations.push(webOperation);
            }
        }

        // console.log("getAllFileOperation", fileOperations);
        return webOperations;
    }

    const onTabValueChange = (value: string) => {
        setTabValue(value);
    };

    // 使用useMemo优化currentMessage的计算，避免不必要的重新渲染
    const currentMessage = useMemo(() => {
        if (!processedMessages || processedMessages.length === 0) {
            return null;
        }
        return processedMessages[sliderValue];
    }, [processedMessages, sliderValue]);

    // 使用useMemo优化actionName的计算
    const actionName = useMemo(() => {
        if (!currentMessage) {
            return '';
        } else {
            return currentMessage.action?.name || '';
        }
    }, [currentMessage]);

    // 使用useMemo优化各种operation的计算结果，避免重复计算
    const currentFileOperation = useMemo(() => {
        if (!currentMessage) return undefined;
        return getFileOperation(currentMessage);
    }, [currentMessage]);

    const currentTerminalOperation = useMemo(() => {
        if (!currentMessage) return undefined;
        return getTerminalOperation(currentMessage);
    }, [currentMessage]);

    const currentWebOperation = useMemo(() => {
        if (!currentMessage) return undefined;
        return getWebOperation(currentMessage);
    }, [currentMessage]);

    const allFileOperations = useMemo(() => {
        return getAllFileOperation(processedMessages);
    }, [processedMessages]);

    const allTerminalOperations = useMemo(() => {
        return getAllTerminalOperation(processedMessages);
    }, [processedMessages]);

    const allWebOperations = useMemo(() => {
        return getAllWebOperation(processedMessages);
    }, [processedMessages]);

    // function OperationNotice({ action }: ProcessedMessage) {
    //     const actionName = action?.name || '';
    //     const isTerminal = isTerminalAction(actionName);
    //     const isFile = isFileAction(actionName);

    //     return (
    //         <div className="flex flex-row items-center p-2 gap-0 rounded-lg bg-[url(/工作台卡片.png)] bg-cover bg-top">
    //             <div className="p-1 bg-gray-100 rounded-lg mr-1 w-10 h-10 flex justify-center items-center">
    //                 {React.createElement(getToolIcon(action.name || ''), { className: "h-fit w-fit" })}
    //             </div>

    //             <div className="flex flex-col ml-1">
    //                 <div className="text-sm text-muted-foreground">正在使用 {formatToolName(actionName)}</div>
    //                 <TooltipProvider>
    //                     <Tooltip>
    //                         <TooltipTrigger>
    //                             {isTerminal ? (
    //                                 <Badge variant="outline" className="mt-1 w-fit font-mono text-sm px-2 py-1 max-w-100">
    //                                     <p>
    //                                         正在执行命令
    //                                     </p>
    //                                     <code>{truncateString(getToolKeyParams(action), 20)}</code>
    //                                 </Badge>
    //                             ) : isFile ? (
    //                                 <Badge variant="outline" className="mt-1 w-fit font-mono text-sm px-2 py-1 max-w-100">
    //                                     正在 {action?.arguments.operation} 文件<code>{truncateString(getToolKeyParams(action), 20)}</code>
    //                                 </Badge>
    //                             ) : (
    //                                 <Badge variant="outline" className="mt-1 w-fit font-mono text-sm px-2 py-1 max-w-100">
    //                                     正在调用工具: <code>{truncateString(formatToolName(actionName), 20)}</code>
    //                                 </Badge>
    //                             )}
    //                         </TooltipTrigger>
    //                         {getToolKeyParams(action) && (
    //                             <TooltipContent>
    //                                 <p>{getToolKeyParams(action)}</p>
    //                             </TooltipContent>
    //                         )}
    //                     </Tooltip>
    //                 </TooltipProvider>

    //             </div>
    //         </div>
    //     )
    // }

    const tabClassName = 'px-4 py-2 bg-linear-122 from-[#EFF3FC] via-[#FDFEFF6B] to-[#F9FAFE19] '
    const tabActiveClassName = 'data-[state=active]:shadow-none data-[state=active]:border-none data-[state=active]:-bg-linear-90 data-[state=active]:from-[#5991FF] data-[state=active]:via-[#73AAFF] data-[state=active]:to-[#AFD4FF] data-[state=active]:text-white'

    //     const RenderDesktop = React.memo(function RenderDesktop(props: UserMessageProps) {

    //     }, (prevProps, nextProps) => {
    //     // 自定义比较函数，只在真正变化时重新渲染
    //     return prevProps.message === nextProps.message
    // });

    return (
        <Tabs value={tabValue} onValueChange={onTabValueChange} className="flex flex-col h-full w-full">
            <Card className={`h-full w-full flex flex-col gap-0 rounded-lg border-none shadow-none ${className} bg-[url(/工作台背景.png)] bg-cover bg-top bg-transparent`}>
                <CardHeader className="pb-2">
                    <CardTitle>
                        <div className="flex flex-col gap-4">
                            <div className="font-[PingFang_SC] flex flex-row items-center gap-2">
                                <Image
                                    className="transition-all duration-200"
                                    width="25"
                                    height="25"
                                    src="/工作台icon.png"
                                    alt="Send"
                                />工作台
                            </div>

                            <div>
                                <TabsList className="bg-transparent gap-3 w-fit font-[PingFang_SC]">
                                    {/* <TabsTrigger disabled value="group" className="h-auto data-[state=active]:shadow-none px-4 py-1 bg-white/40 border-1">群组</TabsTrigger> */}
                                    {agentState.browser_use_steps && Object.keys(agentState.browser_use_steps).length > 0 && (
                                        <TabsTrigger value="browser_use" className={`h-auto text-xs font-normal ${tabClassName} ${tabActiveClassName}`}>浏览器沙箱</TabsTrigger>
                                    )}
                                    {allWebOperations && allWebOperations.length > 0 && (
                                        <TabsTrigger value="browser" className={`h-auto text-xs font-normal ${tabClassName} ${tabActiveClassName}`}>浏览器</TabsTrigger>
                                    )}
                                    {allTerminalOperations && allTerminalOperations.length > 0 && (
                                        <TabsTrigger value="terminal" className={`h-auto text-xs font-normal ${tabClassName} ${tabActiveClassName}`}>终端</TabsTrigger>
                                    )}
                                    {allFileOperations && allFileOperations.length > 0 && (
                                        <TabsTrigger value="file" className={`h-auto text-xs font-normal ${tabClassName} ${tabActiveClassName}`}>文件</TabsTrigger>
                                    )}
                                    {/* <TabsTrigger disabled value="tool" className="h-auto data-[state=active]:shadow-none px-4 py-1 bg-white/40 border-1">工具</TabsTrigger> */}
                                </TabsList>
                            </div>
                        </div>

                    </CardTitle>
                </CardHeader>
                {/* 此处不需要加h-full，因为CardContent会自动填充剩余空间 */}
                <CardContent className="flex-grow pt-2 pb-4 w-full overflow-hidden">
                    <TabsContent value="desktop" className="flex-1 w-full h-full">
                        {currentMessage ? (
                            isTerminalAction(actionName) ? (
                                <TerminalTask key={sliderValue} operation={currentTerminalOperation} />
                            ) : isFileAction(actionName) ? (
                                <FilesTask key={sliderValue} operation={currentFileOperation} workingDirectory="/workspace" sandboxId={sandboxId || undefined} />
                            ) : isWebSearchTool(actionName) ? (
                                <WebTask key={sliderValue} operation={currentWebOperation} />
                            ) : (
                                <></>
                            )
                        ) : (
                            <div className="flex flex-col items-center justify-center h-32 text-zinc-400 dark:text-zinc-600">
                                <span>暂无工具调用</span>
                            </div>
                        )}
                    </TabsContent>
                    <TabsContent value="group" className="flex-1">

                    </TabsContent>
                    <TabsContent value="browser_use" className="flex-1 w-full h-full">
                        {agentState.browser_use_steps && Object.keys(agentState.browser_use_steps).length > 0 && (
                            <BrowserUseTask
                                steps={agentState.browser_use_steps}
                            />
                        )}
                    </TabsContent>
                    <TabsContent value="browser" className="flex-1 w-full h-full">
                        {allWebOperations && allWebOperations.length > 0 ? (
                            <WebTask key={allWebOperations.length + 'webTask'} operation={allWebOperations} />
                        ) : (
                            <div className="flex flex-col items-center justify-center h-32 text-zinc-400 dark:text-zinc-600">
                                <span>暂无工具调用</span>
                            </div>
                        )}
                    </TabsContent>
                    <TabsContent value="terminal" className="flex-1 w-full h-full">
                        {allTerminalOperations && allTerminalOperations.length > 0 ? (
                            <TerminalTask operation={allTerminalOperations} />
                        ) : (
                            <div className="flex flex-col items-center justify-center h-32 text-zinc-400 dark:text-zinc-600">
                                <span>暂无工具调用</span>
                            </div>
                        )}
                    </TabsContent>
                    <TabsContent value="file" className="flex-1 w-full h-full">
                        {allFileOperations && allFileOperations.length > 0 ? (
                            <FilesTask operation={allFileOperations} workingDirectory="/workspace" sandboxId={sandboxId || undefined} />
                        ) : (
                            <div className="flex flex-col items-center justify-center h-32 text-zinc-400 dark:text-zinc-600">
                                <span>暂无工具调用</span>
                            </div>
                        )}
                    </TabsContent>
                    <TabsContent value="tool" className="flex-1">

                    </TabsContent>
                </CardContent>
                {tabValue === "desktop" && (
                    <CardFooter className="flex flex-col justify-start items-start gap-2 bg-transparent">
                        <div className="flex flex-row items-center">
                            <Button onClick={handleDecrement} size="medium" shape="circle" variant="text" disabled={!processedMessages || processedMessages.length === 0 || sliderValue === 0} ><PreviousFilledIcon /></Button>
                            <Button onClick={handleIncrement} size="medium" shape="circle" variant="text" disabled={!processedMessages || processedMessages.length === 0 || sliderValue >= processedMessages.length - 1} ><NextFilledIcon /></Button>
                        </div>
                        <Slider
                            className="mx-2"
                            min={0}
                            max={Math.max(0, (processedMessages?.length || 1) - 1)}
                            step={1}
                            value={[sliderValue]}
                            onValueChange={(value) => { if (value[0] != manualSliderValue) { setManualSliderValue(value[0]) } }}
                            disabled={!processedMessages || processedMessages.length <= 1}
                        />
                    </CardFooter>
                )}
            </Card>
        </Tabs>
    )
}
