"use client";

import "tdesign-react/es/_util/react-19-adapter";
import { useCopilotAction, useCopilotChatInternal, CatchAllActionRenderProps } from "@noahlocal/copilotkit-react-core";
import { Role } from "@noahlocal/copilotkit-runtime-client-gql";
import { CopilotChat, UserMessageProps, AssistantMessageProps } from "@noahlocal/copilotkit-react-ui";
import { AIMessage, Message } from "@noahlocal/copilotkit-shared";
import { ThreadStatus } from "@langchain/langgraph-sdk";
import {
    Loader2,
    FileText,
    ChevronDown,
    Compass,
    CircleChevronUp,
    PencilLine,
    Globe,
    Terminal,
    Mouse,
    Keyboard,
    Globe2,
    Share2,
    Copy,
    Check,
    SquareChartGantt
} from "lucide-react";
import { v4 as uuidv4 } from 'uuid';
import React, { useState, useEffect, useCallback, memo, useMemo, useRef } from "react";
import { StopCircleIcon } from 'tdesign-icons-react';
import { NotificationPlugin, TooltipLite, Popup } from 'tdesign-react';
import { motion, AnimatePresence, easeOut } from "framer-motion";
import Image from 'next/image'

import { Button } from "@/components/ui/button";
import { Accordion, AccordionItem, AccordionTrigger, AccordionContent } from "@/components/ui/accordion";
import { MarkdownText } from "@/components/assistant-ui/markdown-text";
import { useSidebar } from "@/components/ui/sidebar";
import { Task } from "@/components/task/task";
import { PlanView } from "@/components/plan/plan";
import { SandboxView } from "@/components/sandbox";
import { MessageToolContent } from "@/components/chat/message-tool-content";
import { ComputerSearchView } from "@/components/computer/search";

import { FileUploader } from "./file-uploader";

import { useAgentContext } from "@/lib/agent-context";
import { replaceImageLinks } from "@/lib/url-replace";
// 导入动画变体
import {
    buttonVariants,
    sidebarVariants,
    slideDownVariants,
} from "@/lib/animations";
import { useModeContext } from "@/lib/mode-context";
import { useLoading } from "@/lib/loading-context";
import { useMessageContext } from "@/lib/message-context";
import { apiClient } from "@/lib/api-client";
import { useAttachmentContext } from "@/lib/attachment-context";

import { AGENT_TYPE, AgentState } from "@/types/agent";
import { formatFileSizeAuto } from "@/utils/file";
import { showWebMessage } from "@/utils/message";
import { CASE_MESSAGE, CASE_TYPE } from "@/cases";

// 定义案例相关的类型
interface CaseItem {
    type: CASE_TYPE;
    content: Message | any;
    state: Record<string, any>;
}

interface ShowCaseState {
    messages: Message[];
    logs: any[];
    messageQueue: string;
    currentId: number;
    structure_tool_results: Record<string, any>;
}

interface GenericToolRenderProps {
    name: string;
    status: string;
    args: any;
}

// 定义右侧面板的类型
type RightPanelMode = 'task' | 'sandbox' | 'plan' | 'hidden';

const FILE_MAP = {
    "doc": "/file-doc.svg",
    "docx": "/file-doc.svg",
    "xls": "/file-xls.svg",
    "xlsx": "/file-xls.svg",
    "ppt": "/file-ppt.svg",
    "pptx": "/file-ppt.svg",
    "pdf": "/file-pdf.svg",
    "txt": "/file-txt.svg",
}

// 工具配置映射
const toolConfigs = {
    files: {
        icon: <PencilLine className="w-4 h-4" />,
        getTitle: (status: string, args: any) => {
            const operationText = {
                create: "创建文件",
                read: "读取文件",
                list: "列出目录",
                delete: "删除文件",
                write: "写入文件",
                mkdir: "创建目录",
                replace: "替换文件内容",
                watch: "监视目录",
                batch_write: "批量写入文件"
            };
            const chineseOperation = operationText[args.operation as keyof typeof operationText] || args.operation;
            return `${status === 'inProgress' ? '正在' : '已完成'}${chineseOperation}${args.path ? ` ${args.path}` : ''}`;
        },
        getParams: () => <></>
    },
    web: {
        icon: <Globe className="w-4 h-4" />,
        getTitle: (status: string, args: any) => {
            const operationText = {
                search: "网络搜索",
                scrape: "提取网页内容"
            };
            const chineseOperation = operationText[args.operation as keyof typeof operationText] || "正在使用浏览器工具";
            let details = '';
            if (args.sub_queries?.[0]?.query) {
                const query = args.sub_queries[0].query;
                details = `: ${query.substring(0, 30)}${query.length > 30 ? "..." : ""}`;
            } else if (args.urls?.[0]) {
                const url = args.urls[0];
                details = `: ${url.substring(0, 30)}${url.length > 30 ? "..." : ""}`;
            }
            return `${status === 'inProgress' ? '正在' : '已完成'}${chineseOperation}${details}`;
        },
        getParams: () => <></>
    },
    execute_command: {
        icon: <Terminal className="w-4 h-4" />,
        getTitle: (status: string, args: any) => {
            let details = '';
            if (args.command) {
                details = `: ${args.command.substring(0, 30)}${args.command.length > 30 ? "..." : ""}`;
            }
            return `${status === 'inProgress' ? '正在' : '已完成'}执行命令${details}`;
        },
        getParams: (args: any, result: any) => {
            console.log('execute_command', args, result)
            const text = '```shell\n' + args.command + '\n```';
            return (
                <MarkdownText className={`max-h-60 flex flex-col custom-scrollbar border border-gray-300/20 rounded-md bg-indigo-100/40'}`}>{text}</MarkdownText>
            );
        }
    },
    computer_use_mouse: {
        icon: <Mouse className="w-4 h-4" />,
        getTitle: (status: string) => `${status === 'inProgress' ? '正在' : '已完成'}控制鼠标`,
        getParams: () => <></>
    },
    computer_use_keyboard: {
        icon: <Keyboard className="w-4 h-4" />,
        getTitle: (status: string) => `${status === 'inProgress' ? '正在' : '已完成'}控制键盘`,
        getParams: () => <></>
    },
    browser: {
        icon: <Globe2 className="w-4 h-4" />,
        getTitle: (status: string) => `${status === 'inProgress' ? '正在' : '已完成'}操作浏览器`,
        getParams: () => <></>
    },
    expose_port: {
        icon: <Share2 className="w-4 h-4" />,
        getTitle: (status: string, args: any) => `${status === 'inProgress' ? '正在' : '已完成'}暴露端口${args.port ? `: ${args.port}` : ''}`,
        getParams: () => <></>
    }
};

// 获取工具配置，如果没有找到则使用默认配置
const getToolConfig = (name: string) => {
    return toolConfigs[name as keyof typeof toolConfigs] || {
        icon: <Terminal className="w-4 h-4" />,
        getTitle: () => `执行 ${name} 工具`,
        getParams: (args: any, results: any) => {
            let text = "";

            try {
                if (args.args) {
                    text = JSON.stringify(args.args, null, 2);
                } else {
                    text = JSON.stringify(args, null, 2);
                }
            } catch {
                text = args;
            }
            return (
                <div className="w-full flex flex-col gap-2 overflow-hidden ">
                    <div className="w-full flex flex-col overflow-hidden rounded-md shadow-[0_0_1px_0_rgba(201,201,201,0.5)] ">
                        <div className="flex flex-row bg-gray-800/5 px-3 py-1 font-[PingFang_SC] text-sm text-[#363B64] justify-between items-center">
                            <span>执行参数</span>
                            <motion.div
                                className="cursor-pointer"
                                variants={{
                                    idle: { scale: 1 },
                                    hover: { scale: 1.05, color: "#000" },
                                    tap: { scale: 0.95, color: "#000" },
                                }}
                                initial="idle"
                                whileHover="hover"
                                whileTap="tap"
                                onClick={() => {
                                    navigator.clipboard.writeText(text);
                                    NotificationPlugin.success({
                                        title: '复制成功',
                                        placement: 'top-right',
                                        duration: 1000,
                                        offset: [-10, 10],
                                        closeBtn: true,
                                    });
                                }}
                            >
                                <Copy className="w-4 h-4 " />
                            </motion.div>
                        </div>
                        {/* <MarkdownText className='max-h-60 flex flex-col custom-scrollbar bg-white/50'>{text}</MarkdownText> */}
                        <pre className="max-h-40 bg-white/50 overflow-auto p-2">
                            {text}
                        </pre>
                    </div>
                    {results.length > 0 && results.map((result: any, index: number) => (
                        <div key={index} className="w-full flex flex-col overflow-hidden rounded-md shadow-[0_0_1px_0_rgba(201,201,201,0.5)]">
                            <div className="flex flex-row bg-gray-800/5 px-3 py-1 font-[PingFang_SC] text-sm text-[#363B64] justify-between items-center">
                                <span>执行结果</span>
                                <motion.div
                                    className="cursor-pointer"
                                    variants={{
                                        idle: { scale: 1 },
                                        hover: { scale: 1.05, color: "#000" },
                                        tap: { scale: 0.95, color: "#000" },
                                    }}
                                    initial="idle"
                                    whileHover="hover"
                                    whileTap="tap"
                                    onClick={() => {
                                        navigator.clipboard.writeText(result.result);
                                        NotificationPlugin.success({
                                            title: '复制成功',
                                            placement: 'top-right',
                                            duration: 1000,
                                            offset: [-10, 10],
                                            closeBtn: true,
                                        });
                                    }}
                                >
                                    <Copy className="w-4 h-4 " />
                                </motion.div>
                            </div>
                            {/* <MarkdownText className='max-h-60 flex flex-col custom-scrollbar bg-white/50'>{text}</MarkdownText> */}
                            <pre className="max-h-40 bg-white/50 overflow-auto p-2">
                                {result.result}
                            </pre>
                        </div>
                    ))}
                </div>
            );
        }
    };
}

const LogItem = ({ log, index }: { log: any, index: number }) => {
    const [expand, setExpand] = useState(true);
    const isThink = log.think ? true : false;
    const isSubLog = (log.sub_logs && log.sub_logs.length > 0) ? true : false;

    return (
        <div className="bg-linear-200 from-[#f0efff] to-[#f0f4ff] border border-[#D7DCFF33] py-2 px-4 rounded-md" key={index}>
            <div
                className="group flex flex-col items-center align-middle justify-between"
                data-expand={expand ? "true" : "false"}
            >
                <div className="flex flex-row w-full items-center align-middle justify-between">
                    <span className="flex-1 font-[PingFang_SC] font-medium text-sm text-[#363B64] truncate">{log.message}</span>
                    <div className="flex-none flex flex-row items-center gap-2">
                        {!log.done && (<Loader2 className="w-5 h-5 text-blue-500 animate-spin" />)}
                        {(isThink || isSubLog) && <ChevronDown
                            className="transition-transform duration-300 cursor-pointer ease-[cubic-bezier(0.87,_0,_0.13,_1)] group-data-[expand=true]:rotate-180"
                            aria-hidden
                            onClick={() => setExpand(!expand)}
                        />
                        }
                    </div>
                </div>
                {isThink && expand &&
                    <MarkdownText className={'max-h-30 p-3 mt-2 bg-white/50 backdrop-blur-md rounded-md text-xs text-gray-500 custom-scrollbar border-1 border-white shadow-[0_0_1px_0_rgba(201,201,201,0.5)]'}>{log.think || log.think.content}</MarkdownText>
                }
                {isSubLog && expand &&
                    <div className="p-3 mt-2 w-full flex flex-col gap-1 bg-white/50 backdrop-blur-md rounded-md border-1 border-white shadow-[0_0_1px_0_rgba(201,201,201,0.5)] custom-scrollbar">
                        {log.sub_logs.map((subLog: any, subIndex: number) => (
                            <div key={subIndex} className="w-full text-xs text-gray-500 flex flex-row justify-between items-center gap-1">
                                <Popup trigger="hover" showArrow content={subLog.message}>
                                    <span className="flex-1 font-[PingFang_SC] truncate cursor-pointer" onClick={() => {
                                        navigator.clipboard.writeText(subLog.message);
                                        NotificationPlugin.success({
                                            title: '复制成功',
                                            placement: 'top-right',
                                            duration: 1000,
                                            offset: [-10, 10],
                                            closeBtn: true,
                                        });
                                    }}>{subLog.message}</span>
                                </Popup>
                                <div className="flex-none flex flex-row items-center gap-2">
                                    {subLog.done ? (
                                        <Check className="w-4 h-4" />
                                    ) : (
                                        <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                }
            </div>
        </div>
    );
};

export const Chat = React.memo(function Chat({ threadId, threadStatus, caseId = "" }: { threadId: string, threadStatus: ThreadStatus, caseId: string }) {
    const { setLoading } = useLoading() // 使用loading-context
    const [isCancelRunning, setIsCancelRunning] = useState(false);
    // const {
    //     availableAgents,
    // } = useCopilotContext();

    const { mode } = useModeContext();

    // 使用SandboxContext获取sandboxId
    const { sandboxId, agentState, setAgentState } = useAgentContext();
    const {
        messages,
        stopGeneration,
        setMessages,
        sendMessage,
        isLoading: isCopliotLoading,
        interrupt
    } = useCopilotChatInternal({ id: threadId });

    const [isCaseRunning, setIsCaseRunning] = useState(false);

    const { isInit, getMessage, getAgentInfo } = useMessageContext();

    useEffect(() => {
        if (caseId) {
            const caseData = CASE_MESSAGE[caseId as keyof typeof CASE_MESSAGE];
            if (caseData) {
                setIsCaseRunning(true);
                showCase(caseData.slice(1) as CaseItem[], [], [], {}, "", 0);
            }
        }
        if (isInit()) {
            const { mode, agentType, files } = getAgentInfo();

            setAgentState(prevState => {
                return {
                    ...prevState,
                    status: 'running',
                    files: files,
                    mode,
                    agent_type: agentType as AGENT_TYPE
                } as AgentState;
            });

            sendMessage({
                id: uuidv4(),
                role: Role.User,
                content: getMessage(),
            });
        }
    }, [])

    // 案例处理器策略
    const caseHandlers = useMemo(() => ({
        "message": (currentCase: CaseItem, state: ShowCaseState) => {
            const { messageQueue, messages } = state;
            const content = currentCase.content.content;
            const CHUNK_SIZE = 3;

            if (messageQueue === "") {
                // 首次显示消息
                const newMessageQueue = content.slice(CHUNK_SIZE);
                const firstMessage = {
                    ...currentCase.content,
                    content: content.slice(0, CHUNK_SIZE)
                };
                return {
                    ...state,
                    messages: [...messages, firstMessage as Message],
                    messageQueue: newMessageQueue,
                    currentId: newMessageQueue === "" ? state.currentId + 1 : state.currentId,
                    timeout: 100
                };
            } else {
                // 继续显示消息
                const newMessageQueue = messageQueue.slice(CHUNK_SIZE);
                const lastMessage = messages[messages.length - 1];
                const updatedMessage = {
                    ...currentCase.content,
                    content: lastMessage.content + messageQueue.slice(0, CHUNK_SIZE)
                };
                return {
                    ...state,
                    messages: [...messages.slice(0, -1), updatedMessage as Message],
                    messageQueue: newMessageQueue,
                    currentId: newMessageQueue === "" ? state.currentId + 1 : state.currentId,
                    timeout: 100
                };
            }
        },

        "message-user": (currentCase: CaseItem, state: ShowCaseState) => ({
            ...state,
            messages: [...state.messages, currentCase.content as Message],
            currentId: state.currentId + 1,
            timeout: 1000
        }),

        "message-file": (currentCase: CaseItem, state: ShowCaseState) => ({
            ...state,
            messages: [...state.messages, currentCase.content as Message],
            currentId: state.currentId + 1,
            timeout: 100
        }),

        "message-terminal": (currentCase: CaseItem, state: ShowCaseState) => ({
            ...state,
            messages: [...state.messages, currentCase.content as Message],
            currentId: state.currentId + 1,
            timeout: 100
        }),

        "message-web": (currentCase: CaseItem, state: ShowCaseState) => ({
            ...state,
            messages: [...state.messages, currentCase.content as Message],
            currentId: state.currentId + 1,
            timeout: 100
        }),

        "message-web-result": (currentCase: CaseItem, state: ShowCaseState) => ({
            ...state,
            structure_tool_results: { ...state.structure_tool_results, ...currentCase.content },
            currentId: state.currentId + 1,
            timeout: 100
        }),

        "message-design": (currentCase: CaseItem, state: ShowCaseState) => ({
            ...state,
            messages: [...state.messages, currentCase.content as Message],
            currentId: state.currentId + 1,
            timeout: 100
        }),

        "message-tool": (currentCase: CaseItem, state: ShowCaseState) => ({
            ...state,
            messages: [...state.messages, currentCase.content as Message],
            currentId: state.currentId + 1,
            timeout: 100
        }),

        "log-new": (currentCase: CaseItem, state: ShowCaseState) => ({
            ...state,
            logs: [...state.logs, currentCase.content],
            currentId: state.currentId + 1,
            timeout: 1000
        }),

        "log-previous": (currentCase: CaseItem, state: ShowCaseState) => ({
            ...state,
            logs: [...state.logs.slice(0, -1), currentCase.content],
            currentId: state.currentId + 1,
            timeout: 1000
        }),
    }), []);

    // 使用 useRef 来存储定时器 ID，以便清理
    const timeoutRef = useRef<NodeJS.Timeout | null>(null);

    const showCase = useCallback((
        cases: CaseItem[],
        showMessages: Message[],
        showLogs: any[],
        showStructureToolResults: Record<string, any>,
        message_queue: string,
        currentId: number
    ) => {
        try {
            // 清理之前的定时器
            if (timeoutRef.current) {
                clearTimeout(timeoutRef.current);
                timeoutRef.current = null;
            }

            // 边界检查和参数验证
            if (!Array.isArray(cases) || cases.length === 0) {
                console.warn('showCase: cases array is empty or invalid');
                setIsCaseRunning(false);
                return;
            }

            if (currentId >= cases.length || currentId < 0) {
                console.warn(`showCase: currentId ${currentId} is out of bounds (0-${cases.length - 1})`);
                setIsCaseRunning(false);
                return;
            }

            if (!Array.isArray(showMessages) || !Array.isArray(showLogs)) {
                console.warn('showCase: showMessages or showLogs is not an array');
                setIsCaseRunning(false);
                return;
            }

            const currentCase = cases[currentId];
            if (!currentCase || typeof currentCase !== 'object') {
                console.warn(`showCase: invalid case at index ${currentId}`);
                setIsCaseRunning(false);
                return;
            }

            if (!currentCase.type || typeof currentCase.type !== 'string') {
                console.warn(`showCase: case at index ${currentId} has invalid type`);
                setIsCaseRunning(false);
                return;
            }

            // 设置初始状态
            const initialState: ShowCaseState = {
                messages: showMessages,
                logs: showLogs,
                messageQueue: message_queue || "",
                structure_tool_results: showStructureToolResults,
                currentId
            };

            // 使用策略模式处理不同类型的案例
            const handler = caseHandlers[currentCase.type as keyof typeof caseHandlers];
            if (!handler) {
                console.warn(`showCase: unknown case type: ${currentCase.type}`);
                setIsCaseRunning(false);
                return;
            }

            // 获取处理结果
            const newState = handler(currentCase, initialState);

            // 验证处理结果
            if (!newState || typeof newState !== 'object') {
                console.warn('showCase: handler returned invalid state');
                setIsCaseRunning(false);
                return;
            }

            // 批量更新状态，减少重渲染
            const stateUpdates: { messages?: Message[]; logs?: any[]; structure_tool_results?: Record<string, any> } = {};

            if (newState.messages !== showMessages && Array.isArray(newState.messages)) {
                stateUpdates.messages = newState.messages;
            }

            if (newState.logs !== showLogs && Array.isArray(newState.logs)) {
                stateUpdates.logs = newState.logs;
            }

            if (newState.structure_tool_results !== showStructureToolResults && Object.keys(newState.structure_tool_results).length > 0) {
                stateUpdates.structure_tool_results = newState.structure_tool_results;
            }

            // 一次性更新所有状态
            if (stateUpdates.messages) {
                setMessages(stateUpdates.messages);
            }

            if (stateUpdates.logs) {
                setAgentState(prevState => {
                    return {
                        ...prevState,
                        logs: stateUpdates.logs
                    } as AgentState;
                });
            }

            if (stateUpdates.structure_tool_results) {
                setAgentState(prevState => {
                    return {
                        ...prevState,
                        structure_tool_results: stateUpdates.structure_tool_results
                    } as AgentState;
                });
            }

            // 递归调用下一个案例
            const nextTimeout = Math.max(0, newState.timeout || 1000); // 确保超时时间非负
            timeoutRef.current = setTimeout(() => {
                if (newState.currentId < cases.length && newState.currentId >= 0) {
                    showCase(
                        cases,
                        newState.messages,
                        newState.logs,
                        newState.structure_tool_results,
                        newState.messageQueue,
                        newState.currentId
                    );
                } else {
                    setIsCaseRunning(false);
                }
            }, nextTimeout);
        } catch (error) {
            console.error('showCase: error occurred:', error);
            // 清理定时器，防止内存泄漏
            if (timeoutRef.current) {
                clearTimeout(timeoutRef.current);
                timeoutRef.current = null;
            }
            setIsCaseRunning(false);
        }
    }, [caseHandlers, setMessages, setAgentState, agentState])

    // 清理定时器
    useEffect(() => {
        return () => {
            if (timeoutRef.current) {
                clearTimeout(timeoutRef.current);
                setIsCaseRunning(false);
            }
        };
    }, []);

    // 修改状态变量，控制右侧面板的显示模式
    const [rightPanelMode, setRightPanelMode] = useState<RightPanelMode>('hidden');
    const toolCallMessagesCountRef = useRef<number>(0);
    const hasShowPlanPanelRef = useRef<boolean>(false); // 判断是否显示过规划面板
    const { attachmentList } = useAttachmentContext();

    const { title: ThreadTitle } = useSidebar();

    console.log("重新加载Chat", threadId, sandboxId, messages, agentState, interrupt);

    useEffect(() => {
        setLoading(false);
    }, [threadId])

    // 切换到规划面板
    const showPlanPanel = useCallback(() => {
        setRightPanelMode(rightPanelMode === 'plan' ? 'hidden' : 'plan');
    }, [rightPanelMode]);

    // 切换到任务面板
    const showTaskPanel = useCallback(() => {
        setRightPanelMode(rightPanelMode === 'task' ? 'hidden' : 'task');
    }, [rightPanelMode]);

    // 切换到沙盒面板
    // const showSandboxPanel = useCallback(() => {
    //     setRightPanelMode(rightPanelMode === 'sandbox' ? 'hidden' : 'sandbox');
    // }, [rightPanelMode]);

    const [inputValue, setInputValue] = useState("");

    const handleKeyDown = async (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            await handleSend(inputValue);
        }
    };

    const handleSend = async (message: string) => {
        if (message.trim() === "") {
            NotificationPlugin.error({
                title: '请输入内容',
                placement: 'top-right',
                duration: 3000,
                offset: [-10, 10],
                closeBtn: true,
            });
            return;
        }

        const files: string[] = [];

        // 这里可以添加逻辑来处理选中的工具
        console.log("发送消息:", message);
        console.log("当前状态:", agentState);
        console.log("选中的模式:", mode);
        console.log("上传的附件:", attachmentList.current);

        if (attachmentList.current.length > 0) {
            console.log("存在附件", attachmentList.current);
            for (const attachment of attachmentList.current) {
                if (attachment.status != "completed") {
                    NotificationPlugin.error({
                        title: `存在上传完成的附件: ${attachment.name}`,
                        content: '请等候或刷新状态',
                        placement: 'top-right',
                        duration: 3000,
                        offset: [-10, 10],
                        closeBtn: true,
                    });
                    setLoading(false);
                    return;
                } else {
                    files.push(attachment.savePath);
                }
            }
        }

        setAgentState(prevState => {
            return {
                ...prevState,
                status: 'running',
                files: files,
                mode: mode
            } as AgentState;
        });

        await sendMessage({
            id: uuidv4(),
            role: Role.User,
            content: message,
        });

        setInputValue("");
    };

    const handleStopGeneration = async () => {
        setIsCaseRunning(false);
        setIsCancelRunning(true);
        if (timeoutRef.current) {
            clearTimeout(timeoutRef.current);
            timeoutRef.current = null;
        }
        stopGeneration();
        await apiClient.cancelLangGraphThread(threadId);
        setAgentState(prevState => {
            return {
                ...prevState,
                status: 'canceled'
            } as AgentState;
        });
        setIsCancelRunning(false);
    };

    // 通用工具渲染组件 - 使用memo优化
    const GenericToolRender = memo<GenericToolRenderProps>(function GenericToolRender({ name, status, args }) {
        const [expand, setExpand] = useState(true);
        const { agentState } = useAgentContext();
        const config = getToolConfig(name);

        const result = agentState.mcp_tool_execution_results?.filter((result: any) => result.id === args.id) || [];

        return (
            <div className="h-fit w-fit max-w-full flex-none rounded-md border border-[#D7DCFF33] bg-linear-200 from-[#FCEEFF] to-[#E8EFFF] to-45%">
                <div
                    className="group py-2 px-4 flex flex-col w-full items-center align-middle justify-between"
                    data-expand={expand ? "true" : "false"}
                >
                    <div className="flex flex-row w-full gap-2 items-center align-middle justify-between">
                        <span className="font-[PingFang_SC] font-medium text-sm text-[#363B64]">{config.getTitle(status, args)}</span>
                        {status === "inProgress" ? (
                            <Loader2 className="w-6 h-6 text-blue-500 animate-spin" />
                        ) : (
                            <ChevronDown
                                className="transition-transform duration-300 ease-[cubic-bezier(0.87,_0,_0.13,_1)] group-data-[expand=true]:rotate-180"
                                aria-hidden
                                onClick={() => setExpand(!expand)}
                            />
                        )}
                    </div>
                    {expand && (
                        <div className="self-start w-full flex flex-col gap-2 justify-between py-2 min-h-0">
                            {config.getParams && config.getParams(args, result)}
                        </div>
                    )}
                </div>
            </div>
        );
    });

    const isHiddenSubComponent: (name: string) => boolean = (name: string) => {
        if (
            name.toLowerCase() === "message" ||
            name.toLowerCase() === "agentoutput" ||
            name.toLowerCase().startsWith("computer") ||
            name === 'files' ||
            name === 'execute_command' ||
            name === 'web' ||
            name === 'image' ||
            name === 'deepinsight'
        ) {
            return true;
        }
        return false;
    }

    // 优化通用工具渲染的render函数
    const GenericToolRenderComponent = ({ name, status, args }: CatchAllActionRenderProps<[]>) => {
        // message工具保持单独处理
        if (isHiddenSubComponent(name)) {
            return <></>;
        }

        return <GenericToolRender name={name} status={status} args={args} />;
    };

    // 使用通配符匹配除了message外的所有工具
    useCopilotAction({
        name: "*",
        render: GenericToolRenderComponent,
    });

    // 优化message工具的render函数
    const messageToolRender = useCallback(({ status, args }: { status: string, args: any }) => {
        return (
            <MessageToolContent status={status} args={args} sandboxId={sandboxId || undefined} />
        );
    }, [sandboxId]);

    // message工具渲染 - 保持独立的复杂渲染逻辑
    useCopilotAction({
        name: "message",
        available: "disabled",
        render: messageToolRender,
        followUp: false,
    });

    // 预处理消息状态，使用 useRef 优化缓存
    // const messageStatesRef = useRef(new Map<string, { isStartOfBlock: boolean; isEndOfBlock: boolean }>());

    // 只在 messages 变化时更新缓存
    useEffect(() => {
        const toolCallMessages: AIMessage[] = messages
            .filter((message: Message) => {
                if (message.role === 'assistant' && message.toolCalls) {
                    if (
                        message.name === 'files' ||
                        message.name === 'execute_command' ||
                        showWebMessage(message, agentState.structure_tool_results || {}) ||
                        message.name === 'image' ||
                        message.name === 'deepinsight'
                    ) {
                        return true;
                    }
                    return false;
                }
                return false;
            }) as AIMessage[]

        const expertDesignMessages: AIMessage[] = messages
            .filter((message: Message) => {
                if (message.role === 'assistant' && message.id.startsWith('expert_design')) {
                    return true;
                }
                return false;
            }) as AIMessage[]



        // 如果满足以下条件，则切换到任务面板
        // 1. 工具调用消息不为空
        // 2. 工具调用消息数量发生变化
        // 3. 右侧面板模式为隐藏或规划
        if (expertDesignMessages.length > 0 || (toolCallMessages.length > 0 && toolCallMessagesCountRef.current != toolCallMessages.length && rightPanelMode != 'task')) {
            setRightPanelMode('task');
        }

        // 如果满足以下条件，则切换到规划面板
        // 1. 规划面板不为空
        // 2. 未显示过规划面板
        if (agentState.plan && agentState.plan.steps && agentState.plan.steps.length > 0 && !hasShowPlanPanelRef.current && rightPanelMode != 'plan') {
            setRightPanelMode('plan');
            hasShowPlanPanelRef.current = true;
        }

        toolCallMessagesCountRef.current = toolCallMessages.length;
    }, [messages]);

    // const deleteLatestRun = () => {
    //     setLoading(true, "删除中");
    //     apiClient.getLangGraphRunList(threadId, {}).then((res: any) => {
    //         console.log("获取问答轮次. res: ", res);
    //         if (res.success) {
    //             const runs: Run[] = res.data;
    //             if (runs.length > 0) {
    //                 apiClient.deleteLangGraphRun(threadId, runs[runs.length - 1].run_id).then((res: any) => {
    //                     console.log("删除最新问答轮次. res: ", res);
    //                     if (res.success) {
    //                         NotificationPlugin.success({
    //                             title: '删除成功',
    //                             placement: 'top-right',
    //                             duration: 1000,
    //                             offset: [-10, 10],
    //                             closeBtn: true,
    //                         });
    //                         setLoading(false);
    //                     } else {
    //                         console.error("删除失败(1). res: ", res);
    //                         NotificationPlugin.error({
    //                             title: `删除失败(1)`,
    //                             content: res.message,
    //                             placement: 'top-right',
    //                             duration: 3000,
    //                             offset: [-10, 10],
    //                             closeBtn: true,
    //                         });
    //                         setLoading(false);
    //                     }
    //                 }).catch((err: any) => {
    //                     console.error("删除失败(2). err: ", err);
    //                     NotificationPlugin.error({
    //                         title: `删除失败(2)`,
    //                         content: err,
    //                         placement: 'top-right',
    //                         duration: 3000,
    //                         offset: [-10, 10],
    //                         closeBtn: true,
    //                     });
    //                     setLoading(false);
    //                 });
    //             } else {
    //                 console.error("删除失败(3). runs: ", runs);
    //                 NotificationPlugin.error({
    //                     title: `删除失败(3)`,
    //                     content: '没有可删除的问答轮次',
    //                     placement: 'top-right',
    //                     duration: 3000,
    //                     offset: [-10, 10],
    //                     closeBtn: true,
    //                 });
    //                 setLoading(false);
    //             }
    //         } else {
    //             console.error("删除失败(4). res: ", res);
    //             NotificationPlugin.error({
    //                 title: `删除失败(4)`,
    //                 content: res.message,
    //                 placement: 'top-right',
    //                 duration: 3000,
    //                 offset: [-10, 10],
    //                 closeBtn: true,
    //             });
    //             setLoading(false);
    //         }
    //     }).catch((err: any) => {
    //         console.error("删除失败(5). err: ", err);
    //         NotificationPlugin.error({
    //             title: `删除失败(5)`,
    //             content: err,
    //             placement: 'top-right',
    //             duration: 3000,
    //             offset: [-10, 10],
    //             closeBtn: true,
    //         });
    //         setLoading(false);
    //     });
    // }

    const CustomAssistantMessage = memo<AssistantMessageProps>(function CustomAssistantMessage(props: AssistantMessageProps) {
        const { message, isLoading } = props;

        const [isProgressOpen, setIsProgressOpen] = useState(true);

        const hiddenSubComponent: boolean = isHiddenSubComponent(message?.name || "");
        const subComponent = message?.generativeUI?.();

        const content = message?.content || "";
        const messageId = message?.id || "";

        if (content === "任务已完成") {
            return (
                <div className="relative flex items-center h-auto w-fit ml-10 rounded-xl border-1 border-transparent bg-white bg-clip-padding before:absolute before:rounded-xl before:top-0.5 before:left-0.5 before:right-0.5 before:bottom-0.5 before:-m-1 before:z-[-1] before:bg-linear-to-b before:from-[#A8E6CF] before:to-[#B4E0E8] mb-2">
                    <div className="relative rounded-xl py-2 px-4">
                        <div className="flex items-center gap-2">
                            <Check className="w-4 h-4 text-green-500 flex-shrink-0" />
                            <span className="font-[PingFang_SC] font-medium text-sm text-[#363B64] whitespace-nowrap">已完成</span>
                        </div>
                    </div>
                </div>
            )
        }

        let normalMessage = content;
        let thinkMessage = "";

        // TODO 从<think>***</think>中提取出***,作为thinkMessage。剩下作为normalMessage
        if (content.indexOf("<think>") != -1) {
            if (content.indexOf("<\/think>") != -1) {
                thinkMessage = content.match(/.*?<think>([\s\S]*)<\/think>/)?.[1] || "";
                normalMessage = content.replace(/.*?<think>([\s\S]*)<\/think>/, "");
            } else {
                thinkMessage = content;
                normalMessage = "";
            }
        }

        // 替换回答中的图片URL
        normalMessage = replaceImageLinks(normalMessage || "", sandboxId || "");
        normalMessage = fixContent(normalMessage);

        thinkMessage = thinkMessage.replace("<think>", "").replace("</think>", "");

        const messageStyles = "px-4 rounded-xl pt-2";
        const avatarStyles = "min-h-10 min-w-10";

        const logs = agentState.logs?.filter((log: any) => log.messageId == messageId) || [];

        // 测试用代码
        // thinkMessage = "## 搜索结果分析\n\n根据搜索结果，我找到了一个可靠的天气预报网站，提供了北京未来5天的天气预报信息。以下是具体的天气情况：\n\n### 北京未来5天天气预报\n\n- **08/05 (周二)**:\n  - 天气: 多云\n  - 温度: 31/23°C\n  - 风向风力: 南风 <3级\n\n- **08/06 (周三)**:\n  - 天气: 多云转晴\n  - 温度: 33/24°C\n  - 风向风力: 西北风 <3级\n\n- **08/07 (周四)**:\n  - 天气: 多云\n  - 温度: 32/24°C\n  - 风向风力: 西南风 <3级\n\n- **08/08 (周五)**:\n  - 天气: 阴转雷阵雨\n  - 温度: 28/22°C\n  - 风向风力: 北风 <3级\n\n- **08/09 (周六)**:\n  - 天气: 小雨\n  - 温度: 29/22°C\n  - 风向风力: 东风 <3级\n\n### 数据来源\n- [2025年08月04日北京天气预报](https://bochaai.com/share/81648f5e-2a2b-4137-a9ca-8e2e114d3845)\n\n如果您需要更多详细信息或有其他问题，请告诉我！";

        const avatar = <div className={avatarStyles}></div>
        // 当 message 不为空或存在 subComponent 时才渲染整个区块
        return (content || (!hiddenSubComponent && subComponent) || isLoading) ? (
            <div className="py-2 w-full! overflow-hidden">
                <div className="flex items-start w-full!">
                    {/* {isStartOfBlock && message && avatar} */}
                    {content && avatar}
                    <div className="w-5/6 flex flex-col gap-2 items-start align-center">
                        {/* {isStartOfBlock && message && <div className="flex gap-2 px-4 rounded-xl pt-2 ml-0">
                            <Image src="/智慧助手icon.png" alt="智慧助手icon" width={20} height={20} />
                            <span className="font-[PingFang_SC] text-sm text-zinc-500">聚智AI助手</span>
                        </div>} */}
                        {content && <div className="flex gap-2 px-4 rounded-xl pt-2 ml-0">
                            <Image src="/智慧助手icon.png" alt="智慧助手icon" width={20} height={20} />
                            <span className="font-[PingFang_SC] text-sm text-zinc-500">聚智AI助手</span>
                        </div>}

                        {subComponent && <div className="w-full ml-10">{subComponent}</div>}

                        {isLoading &&
                            <motion.div
                                key="thinking"
                                className="flex items-center gap-1 pb-2 ml-5 mt-5"
                                variants={{
                                    animate: {
                                        opacity: [1, 0.5, 1],
                                        transition: {
                                            duration: 1.2,
                                            repeat: Infinity,
                                            ease: "easeInOut"
                                        }
                                    }
                                }}
                                initial={false}
                                animate="animate"
                            >
                                <Loader2 className="h-4 w-4 animate-spin text-black-500" />
                                <span className="text-sm animate-dot-blink">正在思考</span>
                            </motion.div>
                        }
                        {content && !isLoading && <div className={`w-full flex flex-col gap-2`}>
                            {normalMessage && (
                                <div className={`${messageStyles} ml-0 bg-white border-1 border-zinc-200 w-full`}>
                                    <div className="w-full flex items-center align-center gap-1 pb-2">
                                        <MarkdownText>{normalMessage}</MarkdownText>
                                    </div>
                                </div>
                            )}
                            {thinkMessage &&
                                <div className="px-4 rounded-xl py-2 ml-0 bg-white border-1 border-zinc-200 bg-linear-to-br from-[#E8EFFF] to-[#F9FBFF]">
                                    <Accordion
                                        className=""
                                        defaultValue="think"
                                        type="single"
                                        collapsible
                                    >
                                        <AccordionItem
                                            className="overflow-hidden"
                                            value="think"
                                        >
                                            <AccordionTrigger
                                                className="group w-full flex justify-between items-center hover:no-underline"
                                            >
                                                <div className="flex items-center gap-2">
                                                    <Image src="/thinking.png" alt="thinking" width={20} height={20} />
                                                    <span className="font-[PingFang_SC] text-sm font-bold">思考过程</span>
                                                </div>
                                                <ChevronDown
                                                    className="transition-transform duration-300 ease-[cubic-bezier(0.87,_0,_0.13,_1)] group-data-[state=open]:rotate-180"
                                                    aria-hidden
                                                />
                                            </AccordionTrigger>
                                            <AccordionContent
                                                className="py-2 font-[PingFang_SC] text-black/80 text-sm max-h-50 overflow-y-auto"
                                            >
                                                {thinkMessage}
                                            </AccordionContent>
                                        </AccordionItem>
                                    </Accordion>
                                </div>
                            }
                        </div>
                        }

                        {/* {isCurrentMessage && !isLoading && !isGenerating && <div className="w-full flex flex-row items-center justify-between gap-2">
                            <div></div>
                            <div className="flex flex-row gap-2 items-center justify-end">
                                <motion.button
                                    className="cursor-pointer"
                                    variants={{
                                        idle: { scale: 1, color: "oklch(21% 0.034 264.665)" },
                                        hover: { scale: 1.05, color: "oklch(70.4% 0.191 22.216)" },
                                        tap: { scale: 0.95, color: "oklch(57.7% 0.245 27.325)", rotate: 20, translateY: 2, translateX: 2 }
                                    }}
                                    initial="idle"
                                    whileHover="hover"
                                    whileTap="tap"
                                    onClick={() => {
                                        console.log("不喜欢");
                                    }}
                                >
                                    <ThumbsDown className="w-4 h-4" />
                                </motion.button>
                                <motion.button
                                    className="cursor-pointer"
                                    variants={{
                                        idle: { scale: 1, color: "oklch(21% 0.034 264.665)" },
                                        hover: { scale: 1.05, color: "oklch(70.7% 0.165 254.624)" },
                                        tap: { scale: 0.95, color: "oklch(54.6% 0.245 262.881)", rotate: -20, translateY: -2, translateX: -2 }
                                    }}
                                    initial="idle"
                                    whileHover="hover"
                                    whileTap="tap"
                                    onClick={() => {
                                        console.log("喜欢");
                                    }}
                                >
                                    <ThumbsUp className="w-4 h-4" />
                                </motion.button>
                                <motion.button
                                    className="cursor-pointer"
                                    variants={{
                                        idle: { scale: 1, color: "oklch(21% 0.034 264.665)" },
                                        hover: { scale: 1.05, color: "oklch(70.7% 0.165 254.624)" },
                                        tap: { scale: 0.95, color: "oklch(54.6% 0.245 262.881)", rotate: 360, transition: { duration: 0.5 } }
                                    }}
                                    initial="idle"
                                    whileHover="hover"
                                    whileTap="tap"
                                    onClick={() => {
                                        console.log("重新生成");
                                        reloadMessages(messageId);
                                    }}
                                >
                                    <RotateCcw className="w-4 h-4" />
                                </motion.button>
                                <motion.button
                                    className="cursor-pointer"
                                    variants={{
                                        idle: { scale: 1, color: "oklch(21% 0.034 264.665)" },
                                        hover: { scale: 1.05, color: "oklch(75% 0.183 55.934)" },
                                        tap: { scale: 0.95, color: "oklch(64.6% 0.222 41.116)", rotate: -20, translateY: -2, translateX: -2 }
                                    }}
                                    initial="idle"
                                    whileHover="hover"
                                    whileTap="tap"
                                    onClick={() => {
                                        console.log("删除");
                                        deleteLatestRun();
                                    }}
                                >
                                    <Trash2 className="w-4 h-4" />
                                </motion.button>
                            </div>
                        </div>} */}

                        {/* 执行参数 */}
                        {logs.length > 0 && (
                            <div className="h-fit w-full flex-none py-2 mt-4 mb-2">
                                <div className="flex flex-row items-center justify-between">
                                    <div className="shrink-0 flex items-center gap-2 text-xs text-gray-500"><Compass size={20} /> 执行过程</div>
                                    <div className="flex-1 flex items-center justify-center overflow-hidden mx-2">
                                        <div className="flex gap-0.5 items-center select-none text-gray-400">
                                            {
                                                [...Array(100)].map((_, i) => {
                                                    return <span key={i} >·</span>
                                                })
                                            }
                                        </div>
                                    </div>
                                    <div
                                        className="shrink-0 group flex items-center gap-2 text-xs text-[#1A65FF] cursor-pointer"
                                        onClick={() => { setIsProgressOpen(!isProgressOpen) }}
                                        data-progress={isProgressOpen ? "open" : "closed"}
                                    >
                                        查看执行过程
                                        <CircleChevronUp
                                            className="transition-transform duration-300 ease-[cubic-bezier(0.87,_0,_0.13,_1)] group-data-[progress=open]:rotate-180"
                                            aria-hidden
                                            size={20}
                                        />
                                    </div>
                                </div>
                                <div className="flex flex-col gap-2 mt-2">
                                    {isProgressOpen && logs.map((log: any, index: number) => (
                                        <LogItem key={index} log={log} index={index} />
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                </div>
                {/* {messageData.isTextMessage() && agentState.usage_metadata?.[messageData.id] && <DropdownMenuComponent usageMetadata={agentState.usage_metadata[messageData.id]} />} */}
            </div >
        ) : (
            <></>
        );
    }, (prevProps, nextProps) => {
        // 自定义比较函数，只在真正变化时重新渲染
        return prevProps.message === nextProps.message &&
            prevProps.isLoading === nextProps.isLoading
    });

    const fixContent = (content: string) => {
        // 修复如![](XXX)、![]()的图片链接，修改为![image](XXX)、![image]()
        if (!content) return content;

        // 使用正则表达式匹配![](XXX)和![]()格式的图片链接
        // 这个正则表达式会匹配![](任意内容)和![]()的模式
        return content.replace(/!\[\]\(([^)]*)\)/g, '![点击下载图片]($1)');
    }

    const CustomUserMessage = memo<UserMessageProps>(function CustomUserMessage(props: UserMessageProps) {
        const [isProgressOpen, setIsProgressOpen] = useState(true);
        const { message } = props;
        if (!message) return;
        if (!message.content) return;

        const messageId = message?.id || "";

        const logs = agentState.logs?.filter((log: any) => log.messageId == messageId) || [];

        return (
            <>
                <div className="w-full! flex flex-col items-end gap-2">
                    <div className="flex flex-row gap-2 items-start justify-end mb-4 w-full">
                        <div className="flex flex-col gap-2 w-full justify-end items-end">
                            {/* 用户消息内容 */}
                            <span className="max-w-2/3 text-base bg-linear-to-tl from-[#CEE0FF] to-[#FFF3E9] py-2 px-4 rounded-lg break-words flex-shrink-0">{message.content}</span>
                            {/* 用户消息附件 */}
                            <div className="flex flex-row gap-2 max-w-2/3 overflow-x-auto">
                                {attachmentList.current.map((attachment, index) => {
                                    return (
                                        <div key={index} className="flex flex-row shrink-0 items-center gap-2 p-1 bg-[#F7FAFF] border-1 border-[#EAECF0] rounded-lg">
                                            <img
                                                src={FILE_MAP[attachment.name.split(".").pop() as keyof typeof FILE_MAP] || "/file-attachment.svg"}
                                                alt="file"
                                                className="w-10 h-10 inline-block"
                                            />
                                            <div className="flex flex-col gap-2 font-[PingFang_SC] pr-1 text-xs text-zinc-500 ">
                                                <TooltipLite content={attachment.name} placement="bottom" showArrow>
                                                    <span className="w-20 truncate">
                                                        {attachment.name}
                                                    </span>
                                                </TooltipLite >
                                                <div className="w-20 flex flex-row gap-2 justify-start items-center">
                                                    <span>{attachment.extension}</span>
                                                    <span>{formatFileSizeAuto(Number(attachment.size))}</span>
                                                </div>
                                            </div>
                                        </div>
                                    )
                                })}
                            </div>
                        </div>
                        <Image src="/user-avatar.png" alt="用户头像" width={40} height={40} />
                    </div>
                </div>
                {/* 执行过程 */}
                {logs.length > 0 && (
                    <div className="h-fit w-5/6 items-start flex-none py-2 my-4 ml-10">
                        <div className="flex flex-row items-center justify-between">
                            <div className="shrink-0 flex items-center gap-2 text-xs text-gray-500"><Compass size={20} /> 执行过程</div>
                            <div className="flex-1 flex items-center justify-center overflow-hidden mx-2">
                                <div className="flex gap-0.5 items-center select-none text-gray-400">
                                    {
                                        [...Array(100)].map((_, i) => {
                                            return <span key={i} >·</span>
                                        })
                                    }
                                </div>
                            </div>
                            <div
                                className="shrink-0 group flex items-center gap-2 text-xs text-[#1A65FF] cursor-pointer"
                                onClick={() => { setIsProgressOpen(!isProgressOpen) }}
                                data-progress={isProgressOpen ? "open" : "closed"}
                            >
                                查看执行过程
                                <CircleChevronUp
                                    className="transition-transform duration-300 ease-[cubic-bezier(0.87,_0,_0.13,_1)] group-data-[progress=open]:rotate-180"
                                    aria-hidden
                                    size={20}
                                />
                            </div>
                        </div>
                        <div className="flex flex-col gap-2 mt-2">
                            {isProgressOpen && logs.map((log: any, index: number) => (
                                <LogItem key={index} log={log} index={index} />
                            ))}
                        </div>
                    </div>
                )}
            </>
        );
    }, (prevProps, nextProps) => {
        // 自定义比较函数，只在真正变化时重新渲染
        return prevProps.message === nextProps.message
    });

    return (
        <div className="flex flex-col h-full overflow-y-hidden">
            {/* 新增的 header 栏目 */}
            <AnimatePresence>
                {messages.length > 0 && (
                    <motion.div
                        className="flex justify-between items-center p-4 select-none"
                        variants={slideDownVariants}
                        initial={false}
                        animate="animate"
                        exit="exit"
                    >
                        <div className="flex items-center">
                            <div className="flex items-center bg-[url(/标题.png)] bg-no-repeat ng-center bg-cover px-2 py-1">
                                <Image src="/标题icon.png" alt="标题icon" width={28} height={28} />
                                <span className="font-[PingFang_SC] text-base ml-2 max-w-100 overflow-hidden text-ellipsis whitespace-nowrap">{ThreadTitle}</span>
                            </div>
                            <span className="mx-1 font-[PingFang_SC] text-[#cecad5] opacity-20">|</span>
                            <span className="bg-blue-400/20 px-2 py-1 rounded-sm font-[PingFang_SC] text-[#1a65ff] text-xs">探索模式</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <motion.div
                                variants={buttonVariants}
                                whileHover="hover"
                                whileTap="tap"
                            >
                                <Button
                                    variant={rightPanelMode === 'plan' ? 'default' : 'outline'}
                                    size="sm"
                                    onClick={showPlanPanel}
                                    className="h-8 px-2"
                                >
                                    <SquareChartGantt className="w-4 h-4 mr-1" />
                                    规划
                                </Button>
                            </motion.div>
                            <motion.div
                                variants={buttonVariants}
                                whileHover="hover"
                                whileTap="tap"
                            >
                                <Button
                                    variant={rightPanelMode === 'task' ? 'default' : 'outline'}
                                    size="sm"
                                    onClick={showTaskPanel}
                                    className="h-8 px-2"
                                >
                                    <FileText className="w-4 h-4 mr-1" />
                                    任务
                                </Button>
                            </motion.div>
                            {/* <motion.div
                                variants={buttonVariants}
                                whileHover="hover"
                                whileTap="tap"
                            >
                                <Button
                                    variant={rightPanelMode === 'sandbox' ? 'default' : 'outline'}
                                    size="sm"
                                    onClick={showSandboxPanel}
                                    className="h-8 px-2"
                                >
                                    <Monitor className="w-4 h-4 mr-1" />
                                    沙盒
                                </Button>
                            </motion.div> */}
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
            <AnimatePresence mode="wait">
                <motion.div
                    className={`flex w-full h-full pb-2 overflow-hidden ${rightPanelMode === 'sandbox' ? 'min-w-[1400px]' : rightPanelMode === 'task' ? 'min-w-[1200px]' : 'min-w-[800px]'}`}
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 1.05 }}
                    transition={{ duration: 0.4, ease: easeOut }}
                >
                    <motion.div
                        className={`${rightPanelMode == 'hidden' ? 'w-full' : 'w-1/2'} flex flex-col items-center h-full ml-4 mr-2 overflow-hidden rounded-lg border min-w-[500px]`}
                        animate={{ width: rightPanelMode == 'hidden' ? '100%' : '50%' }}
                        transition={{ duration: 0.3, ease: easeOut }}
                    >

                        {/* 聊天区域 */}
                        {/* 此处虽然可以用messages.map手动实现，但较为原始。相信CopilotKit对于消息的控制有优化得当的地方，所以继续使用CopilotChat组件 */}
                        {/* <div className={`w-full flex-1 p-4 overflow-y-auto ${isComputer ? '' : 'mb-4'} `}>
                            {messages.map((message, index) => {
                                if (message.role === "assistant") {
                                    // console.log("assistant message", message)
                                    return <CustomAssistantMessage key={index} message={message.content || ""} />
                                } else if (message.role === "tool") {
                                    console.log("tool message", message)
                                    return <></>
                                    // return <div key={index}>tool message</div>
                                } else if (message.role === "user") {
                                    // console.log("user message", message)
                                    return <CustomUserMessage key={index} message={message.content || ""} />
                                } else if (message.role === "system") {
                                    console.log("system message", message)
                                    return <></>
                                    // return <div key={index}>system message</div>
                                } else if (message.role === "developer") {
                                    console.log("developer message", message)
                                    return <></>
                                    // return <div key={index}>developer message</div>
                                }
                            })}
                        </div> */}
                        <CopilotChat
                            className="w-full flex-1 overflow-y-auto"
                            instructions={""}
                            labels={{
                                title: "AI助手对话",
                                initial: "",
                            }}
                            onStopGeneration={() => {
                                stopGeneration();
                            }}
                            Input={() => { return <></> }}
                            AssistantMessage={CustomAssistantMessage}
                            UserMessage={CustomUserMessage}
                        />

                        {/* 小电脑 */}
                        <ComputerSearchView threadId={threadId} />

                        <div className='z-10 w-full flex-none px-4 my-2 bg-transparent'>
                            <div className="max-w-4xl mx-auto">
                                {/* 显示当前选中的工具信息 */}
                                {/* {selectedMcpTools.current.length > 0 && (
                                    <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                                        <div className="text-sm text-blue-800 font-medium mb-2">
                                            已选择 {selectedMcpTools.current.length} 个工具:
                                        </div>
                                        <div className="flex flex-wrap gap-2">
                                            {selectedMcpTools.current.map((tool: MCPToolInfo, index: number) => (
                                                <span key={index} className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded">
                                                    {tool.name}
                                                </span>
                                            ))}
                                        </div>
                                    </div>
                                )} */}

                                {(threadStatus === 'error' || (caseId != "" && !isCaseRunning)) ? (
                                    <motion.div
                                        initial={{ opacity: 0, scale: 0.95 }}
                                        animate={{ opacity: 1, scale: 1 }}
                                        exit={{ opacity: 0, scale: 1.05 }}
                                        transition={{ duration: 0.4, ease: easeOut }}
                                    >
                                        <div className="relative flex items-center h-15 w-full rounded-xl border-1 border-transparent bg-white bg-clip-padding before:absolute before:rounded-xl before:top-0.5 before:left-0.5 before:right-0.5 before:bottom-0.5 before:-m-1 before:z-[-1] before:bg-linear-to-b before:from-[#FFBB94] before:to-[#BFC7FF]">
                                            <div className="relative rounded-xl py-3 px-5">
                                                <div
                                                    className="flex items-center text-center justify-between px-7 py-1"
                                                >
                                                    <span className="font-[PingFang_SC] font-medium text-base leading-[22px] text-[#363B64] ">当前会话已结束，可点创建任务开始新的会话</span>
                                                    {/* <Button
                                                asChild
                                                onClick={onStop}
                                                className="flex items-center justify-center rounded-sm transition-all duration-200 bg-[#2E74FD0C] text-[#1A65FF] hover:bg-[#2E74FD0C]/80"
                                            >
                                                <motion.button
                                                    variants={{
                                                        idle: { scale: 1 },
                                                        hover: { scale: 1.05 },
                                                        tap: { scale: 0.95 },
                                                    }}
                                                    initial="idle"
                                                    whileHover="hover"
                                                    whileTap="tap"
                                                >
                                                    <Image src="/stop.png" alt="Stop" width={20} height={20} />
                                                    <span className="font-[PingFang_SC] text-sm">创建新会话</span>
                                                </motion.button>
                                            </Button> */}
                                                </div>
                                            </div>
                                        </div>
                                    </motion.div>
                                ) : (isCancelRunning) ? (
                                    <motion.div
                                        initial={{ opacity: 0, scale: 0.95 }}
                                        animate={{ opacity: 1, scale: 1 }}
                                        exit={{ opacity: 0, scale: 1.05 }}
                                        transition={{ duration: 0.4, ease: easeOut }}
                                    >
                                        <div className="relative flex items-center h-15 w-full rounded-xl border-1 border-transparent bg-white bg-clip-padding before:absolute before:rounded-xl before:top-0.5 before:left-0.5 before:right-0.5 before:bottom-0.5 before:-m-1 before:z-[-1] before:bg-linear-to-b before:from-[#FFBB94] before:to-[#BFC7FF]">
                                            <div className="relative w-full rounded-xl px-5">
                                                <div
                                                    className="flex items-center justify-between px-7 py-1"
                                                >
                                                    <span className="font-[PingFang_SC] font-medium text-base text-[#363B64] after:content-[''] after:animate-dot-blink">正在取消会话中</span>
                                                </div>
                                            </div>
                                        </div>
                                    </motion.div>
                                ) : (agentState.status == 'running' || isCopliotLoading || isCaseRunning) ? (
                                    <motion.div
                                        initial={{ opacity: 0, scale: 0.95 }}
                                        animate={{ opacity: 1, scale: 1 }}
                                        exit={{ opacity: 0, scale: 1.05 }}
                                        transition={{ duration: 0.4, ease: easeOut }}
                                    >
                                        <div className="relative flex items-center h-15 w-full rounded-xl border-1 border-transparent bg-white bg-clip-padding before:absolute before:rounded-xl before:top-0.5 before:left-0.5 before:right-0.5 before:bottom-0.5 before:-m-1 before:z-[-1] before:bg-linear-to-b before:from-[#FFBB94] before:to-[#BFC7FF]">
                                            <div className="relative w-full rounded-xl px-5">
                                                <div
                                                    className="flex items-center justify-between px-7 py-1"
                                                >
                                                    <span className="font-[PingFang_SC] font-medium text-base text-[#363B64] after:content-[''] after:animate-dot-blink flex items-baseline gap-2">
                                                        <motion.div
                                                            className="w-2 h-2 rounded-full"
                                                            style={{
                                                                background: "linear-gradient(135deg, #FF6B6B, #4ECDC4)",
                                                            }}
                                                            animate={{
                                                                y: [0, -10, 0, -2, 0],
                                                                background: [
                                                                    "linear-gradient(135deg, #FF6B6B, #4ECDC4)",
                                                                    "linear-gradient(135deg, #4ECDC4, #45B7D1)",
                                                                    "linear-gradient(135deg, #45B7D1, #96CEB4)",
                                                                    "linear-gradient(135deg, #96CEB4, #FFEAA7)",
                                                                    "linear-gradient(135deg, #FFEAA7, #FF6B6B)",
                                                                ],
                                                            }}
                                                            transition={{
                                                                y: {
                                                                    duration: 0.8,
                                                                    repeat: Infinity,
                                                                    times: [0, 0.3, 0.6, 0.75, 1],
                                                                    ease: ["easeOut", "easeIn", "easeOut", "easeIn"],
                                                                },
                                                                background: {
                                                                    duration: 2,
                                                                    repeat: Infinity,
                                                                    ease: "linear",
                                                                },
                                                            }}
                                                        />
                                                        正在执行任务中
                                                    </span>
                                                    <Button
                                                        asChild
                                                        onClick={handleStopGeneration}
                                                        className="flex items-center justify-center rounded-sm transition-all duration-200 bg-[#2E74FD0C] text-[#1A65FF] hover:bg-[#2E74FD0C]/80"
                                                    >
                                                        <motion.button
                                                            variants={{
                                                                idle: {
                                                                    scale: 1
                                                                },
                                                                hover: {
                                                                    scale: 1.05,
                                                                    backgroundImage: 'linear-gradient(315deg, rgba(46, 116, 253, 0.05), rgba(46, 116, 253, 0.05))'
                                                                },
                                                                tap: { scale: 0.95 },
                                                            }}
                                                            initial="idle"
                                                            whileHover="hover"
                                                            whileTap="tap"
                                                            transition={{ duration: 0.2 }}
                                                        >
                                                            {/* <Image src="/cirlce-stop.png" alt="Stop" width={16.55} height={16.55} /> */}
                                                            <StopCircleIcon size="16px" />
                                                            <span className="font-[PingFang_SC] text-base">停止执行</span>
                                                        </motion.button>
                                                    </Button>
                                                </div>
                                            </div>
                                        </div>
                                    </motion.div>
                                ) : (
                                    <motion.div
                                        initial={{ opacity: 0, scale: 0.95 }}
                                        animate={{ opacity: 1, scale: 1 }}
                                        exit={{ opacity: 0, scale: 1.05 }}
                                        transition={{ duration: 0.4, ease: easeOut }}
                                    >
                                        <div className="relative flex items-center h-fit w-full rounded-xl border-1 border-transparent bg-white bg-clip-padding before:absolute before:rounded-xl before:top-0.5 before:left-0.5 before:right-0.5 before:bottom-0.5 before:-m-1 before:z-[-1] before:bg-linear-to-b before:from-[#FFBB94] before:to-[#BFC7FF]">
                                            <div className="relative w-full h-fit flex flex-col justify-between rounded-xl py-2 px-3">
                                                {/* 输入框 */}
                                                <div className="w-full relative flex">
                                                    <textarea
                                                        value={inputValue}
                                                        onChange={(e) => { setInputValue(e.target.value); }}
                                                        onKeyDown={handleKeyDown}
                                                        placeholder="请在此输入您的问题，按回车键发送"
                                                        className="w-full border-0 bg-transparent text-base/6 font-[PingFang_SC] tracking-widest placeholder:text-gray-400 focus-visible:ring-0 resize-none outline-none px-4 py-2"
                                                        style={{ textIndent: "0em" }}
                                                        rows={2}
                                                    />
                                                </div>

                                                {/* 功能按钮栏 */}
                                                <div className="flex items-center justify-between pt-2">
                                                    {/* 左侧按钮组 */}
                                                    <div className="flex items-center gap-2 ">
                                                        <FileUploader key={threadId} disabled={isCopliotLoading} threadId={threadId} />
                                                    </div>
                                                    {/* 右侧按钮组 */}
                                                    <div className="flex items-center text-center gap-1">
                                                        <Button
                                                            asChild
                                                            variant="outline"
                                                            className="w-20 rounded-sm border-none hover:bg-transparent text-sm shadow-none"
                                                            size="icon"
                                                            onClick={() => handleSend(inputValue)}
                                                        >
                                                            <motion.div
                                                                className="cursor-pointer"
                                                                variants={buttonVariants}
                                                                initial="idle"
                                                                whileHover="hover"
                                                                whileTap="tap"
                                                            >
                                                                <Image
                                                                    className="justify-items-center"
                                                                    src="/send.png"
                                                                    alt="Send"
                                                                    width={56}
                                                                    height={32}
                                                                />
                                                            </motion.div>
                                                        </Button>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </motion.div>
                                )}
                            </div>
                        </div>
                    </motion.div>
                    <AnimatePresence>
                        {(rightPanelMode !== 'hidden') && (
                            <motion.div
                                className={`${rightPanelMode === 'sandbox' ? 'w-2/3' : 'w-1/2'} ml-2 mr-4 mb-3 overflow-y-auto`}
                                variants={sidebarVariants}
                                initial="hidden"
                                animate={rightPanelMode === 'sandbox' ? 'sandbox' : 'visible'}
                                exit="exit"
                            >
                                {rightPanelMode === 'task' ? (
                                    <Task className="h-full w-full" threadId={threadId} />
                                ) : rightPanelMode === 'plan' ? (
                                    <PlanView />
                                ) : (
                                    <SandboxView />
                                )}
                            </motion.div>
                        )}
                    </AnimatePresence>
                </motion.div>
            </AnimatePresence>
        </div>
    );
});
