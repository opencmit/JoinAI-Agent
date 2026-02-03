"use client"

import "tdesign-react/es/_util/react-19-adapter";
import { useState, useEffect, useCallback } from "react";
import { AnimatePresence, motion } from "framer-motion";
import Image from 'next/image';
import { redirect, useSearchParams, RedirectType } from "next/navigation";
import { MessageSquare, Trash, ArrowUpFromLine, ArrowDownFromLine, Dot } from "lucide-react";
import { v4 as uuidv4 } from "uuid";
import { NotificationPlugin } from 'tdesign-react';
import { DotsHorizontalIcon } from "@radix-ui/react-icons";
import { Thread as LanggraphThread, DefaultValues } from "@langchain/langgraph-sdk";

import {
    Sidebar,
    SidebarContent,
    SidebarGroup,
    SidebarGroupContent,
    SidebarGroupLabel,
    SidebarHeader,
    SidebarFooter,
    SidebarTrigger,
    useSidebar,
} from "@/components/ui/sidebar"
import { Button } from "@/components/ui/button"
import { buttonVariants } from "@/lib/animations"
import { Separator } from "@/components/ui/separator";
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem } from "@/components/ui/dropdown-menu";

import { useUserContext } from "@/lib/user-context";
import { useLoading } from "@/lib/loading-context";
import { apiClient } from "@/lib/api-client";
import { useAttachmentContext } from "@/lib/attachment-context";

import { defaultThread, Thread } from "@/types/thread";
import { defaultMetaData, AGENT_TYPE } from "@/types/agent";
import { AttachmentInfo } from "@/types/attachment";

export function AppSidebar() {
    const searchParams = useSearchParams()
    const currentThreadId = searchParams.get('threadId')

    // 使用ThreadContext获取threadId和setThreadId
    const { userId } = useUserContext();
    const { setLoading } = useLoading() // 使用loading-context
    const { setAttachmentList } = useAttachmentContext();

    // 线程列表状态
    const [threads, setThreads] = useState<Thread[]>([]);
    const [topThreads, setTopThreads] = useState<Thread[]>([]);
    const { setTitle, hiddenSidebar } = useSidebar();

    // 删除所有线程的函数
    const deleteAllThreads = () => {
        if (threads.length == 0) {
            return;
        }

        setLoading(true, "清空任务中");

        const tasks: Promise<any>[] = [];

        // TODO 清空时删除知识库和附件

        threads.forEach((thread: Thread) => {
            tasks.push(apiClient.deleteLangGraphThread(thread.id));
        })

        Promise.all(tasks).then(() => {
            NotificationPlugin.success({
                title: '已清空所有任务',
                placement: 'top-right',
                duration: 3000,
                offset: [-10, 10],
                closeBtn: true,
            });
            createNewThread(true);
        }).catch(err => {
            console.error("清空Thread失败. err: ", err);
            NotificationPlugin.error({
                title: '清空任务失败',
                content: '请刷新页面后重试',
                placement: 'top-right',
                duration: 3000,
                offset: [-10, 10],
                closeBtn: true,
            });
            setLoading(false);
        })
    };

    const init = async () => {
        setLoading(true, "获取任务列表中");
        try {
            const res = await apiClient.getLangGraphThreadList({
                metadata: {
                    assistantId: userId
                },
                limit: 100,
                offset: 0,
                sortBy: 'created_at',
                sortOrder: 'desc',
            })
            const data: LanggraphThread<DefaultValues>[] = res.data

            // console.log("获取到ThreaList. data: ", data);
            if (data.length == 0) {
                createNewThread(true);
            } else if (data.length > 0) {
                // 初始化topThreads和threads
                setTopThreads(data.filter((item: LanggraphThread<DefaultValues>) => item.metadata?.top).map((item: LanggraphThread<DefaultValues>) => convertLanggraphThreadToThread(item)));
                setThreads(data.filter((item: LanggraphThread<DefaultValues>) => !item.metadata?.top).map((item: LanggraphThread<DefaultValues>) => convertLanggraphThreadToThread(item)));

                // 获取当前线程
                let selectedLanggraphThread: LanggraphThread<DefaultValues> = data.find((item: LanggraphThread<DefaultValues>) => item.thread_id === currentThreadId) || data[0];
                if (currentThreadId == null) {
                    // 如果currentThreadId为空，则选择第一个线程
                    selectedLanggraphThread = data[0];
                }

                selectThread(selectedLanggraphThread.thread_id);
            }
            setLoading(false);

            handleRefreshThreadState();
        } catch (error) {
            console.error('获取ThreadList失败', error);
            NotificationPlugin.error({
                title: '创建对话列表失败',
                content: '请刷新页面后重试',
                placement: 'top-right',
                duration: 3000,
                offset: [-10, 10],
                closeBtn: true,
            });
            setLoading(false);
        }
    }

    // 检查thread数组是否有内容变化（不仅检查ID，还检查关键属性）
    const hasThreadsChanged = (prev: Thread[], next: Thread[]): boolean => {
        // 如果数量或ID不同，说明有变化
        const prevIds = prev.map(t => t.id).sort().join(',');
        const nextIds = next.map(t => t.id).sort().join(',');
        if (prevIds !== nextIds) {
            return true;
        }

        // 创建prev的映射以便快速查找
        const prevMap = new Map(prev.map(t => [t.id, t]));

        // 检查每个thread的关键属性是否有变化
        for (const nextThread of next) {
            const prevThread = prevMap.get(nextThread.id);
            if (!prevThread) {
                continue; // 新thread已经在ID检查中处理
            }

            // 检查关键属性是否变化
            if (
                prevThread.title !== nextThread.title ||
                prevThread.status !== nextThread.status ||
                prevThread.updatedAt.getTime() !== nextThread.updatedAt.getTime() ||
                prevThread.top !== nextThread.top
            ) {
                return true;
            }
        }

        return false;
    };

    const updateThreadState = useCallback(async (count: number = 0): Promise<void> => {
        // 轮询失败10次，则停止轮询
        if (count > 10) {
            return;
        }

        try {
            const res = await apiClient.getLangGraphThreadList({
                metadata: {
                    assistantId: userId
                },
                limit: 100,
                offset: 0,
                sortBy: 'created_at',
                sortOrder: 'desc',
            })
            const data: LanggraphThread<DefaultValues>[] = res.data

            if (data.length == 0) {
            } else if (data.length > 0) {
                // 智能合并threads状态，而不是直接替换
                const newTopThreads = data
                    .filter((item: LanggraphThread<DefaultValues>) => item.metadata?.top)
                    .map((item: LanggraphThread<DefaultValues>) => convertLanggraphThreadToThread(item));

                const newThreads = data
                    .filter((item: LanggraphThread<DefaultValues>) => !item.metadata?.top)
                    .map((item: LanggraphThread<DefaultValues>) => convertLanggraphThreadToThread(item));

                // 使用函数式更新确保基于最新状态，并检查内容是否有变化
                setTopThreads(prevTopThreads => {
                    // 如果内容有变化，才更新
                    return hasThreadsChanged(prevTopThreads, newTopThreads) ? newTopThreads : prevTopThreads;
                });

                setThreads(prevThreads => {
                    // 如果内容有变化，才更新
                    return hasThreadsChanged(prevThreads, newThreads) ? newThreads : prevThreads;
                });
            }

            // 继续轮询
            setTimeout(() => {
                updateThreadState(count);
            }, 10000);
        } catch (error) {
            console.error('轮询查询thread失败:', error);
            setTimeout(() => {
                updateThreadState(count + 1);
            }, 10000);
        }
    }, [userId]);

    const handleRefreshThreadState = useCallback(async () => {

        await updateThreadState(0);
    }, [updateThreadState]);


    // 初始化加载已保存的线程 - 只在组件挂载时执行一次
    useEffect(() => {
        init();
    }, []); // 空依赖数组，只在挂载时执行一次

    // 创建新线程
    const createNewThread = useCallback(async (init: boolean = false) => {
        setLoading(true, "创建任务中");
        const newThreadId = uuidv4();
        const newThreadTitle = "新对话";

        // 调用接口，创建langgraph对应的thread
        let result: any
        try {
            // 初始化MetaData
            const metaData = {
                ...defaultMetaData,
                title: newThreadTitle,
                assistantId: userId
            };
            console.log('createNewThread', metaData)
            result = await apiClient.createLangGraphThread({
                threadId: newThreadId,
                metadata: metaData
            })
            console.log("成功创建Thread. result: ", result);
        } catch (error: any) {
            console.error("创建Thread失败. err: ", error);
            NotificationPlugin.error({
                title: '创建任务失败',
                content: error,
                placement: 'top-right',
                duration: 3000,
                offset: [-10, 10],
                closeBtn: true,
            });
            setLoading(false);
            return;
        }

        // 初始化页面变量
        initPage();

        // 更新本页面变量
        const newThread = {
            ...defaultThread,
            id: newThreadId,
            title: newThreadTitle,
            createdAt: new Date(result.created_at),
            updatedAt: new Date(result.updated_at),
            status: result.status,
        };

        // 更新
        if (init) {
            setThreads([newThread]);
        } else {
            setThreads(prev => ([
                newThread,
                ...prev,
            ]));
        }

        NotificationPlugin.success({
            title: '创建任务成功',
            placement: 'top-right',
            duration: 3000,
            offset: [-10, 10],
            closeBtn: true,
        });

        redirect(`/chat?threadId=${newThreadId}`, RedirectType.replace);
    }, []);

    function initPage() {
        // 初始化页面变量
        setAttachmentList("", []);
    }

    // 选择线程
    const selectThread = async (threadId: string) => {
        if (threadId == currentThreadId) {
            return;
        }

        setLoading(true, "对话准备中");

        // 获取线程
        const langgraphThread = await apiClient.getLangGraphThreadState(threadId as string);

        // 如果线程不存在，则提示
        if (langgraphThread === null) {
            NotificationPlugin.error({
                title: '任务不存在',
                content: '请刷新页面后重试',
                placement: 'top-right',
                duration: 3000,
                offset: [-10, 10],
                closeBtn: true,
            });
            setLoading(false);
            return;
        }

        const selectedThread = convertLanggraphThreadToThread(langgraphThread);

        // 更新页面变量
        updatePage(selectedThread);

        redirect(`/chat?threadId=${selectedThread.id}`);
    };

    // 更新页面变量
    function updatePage(selectedThread: Thread) {
        console.log('updatePage', selectedThread)

        // 更新对话标题
        setTitle(selectedThread.title);

        // 更新附件相关变量
        setAttachmentList("", selectedThread.attachmentList);
    }


    // 将langgraph的thread转换为Thread类型
    function convertLanggraphThreadToThread(thread: LanggraphThread<DefaultValues>): Thread {
        return {
            id: thread.thread_id,
            title: thread.metadata?.title as string,
            top: thread.metadata?.top as boolean,
            attachmentList: thread.metadata?.attachmentList as AttachmentInfo[] || [],
            agentType: thread.metadata?.agentType as AGENT_TYPE || "normal",
            createdAt: new Date(thread.created_at),
            updatedAt: new Date(thread.updated_at),
            status: thread.status,
            values: thread.values
        }
    }

    // 删除线程
    const onDeleteThread = async (threadId: string) => {
        setLoading(true, "删除任务中");

        try {
            await apiClient.deleteLangGraphThread(threadId)
        } catch (error: any) {
            console.error("删除Thread失败. err: ", error);
            NotificationPlugin.error({
                title: '删除任务失败',
                content: error,
                placement: 'top-right',
                duration: 3000,
                offset: [-10, 10],
                closeBtn: true,
            });
            setLoading(false);
            return;
        }

        const tempLowThreads = threads.filter(thread => thread.id !== threadId)
        setThreads(tempLowThreads);
        const tempTopThreads = topThreads.filter(thread => thread.id !== threadId)
        setTopThreads(tempTopThreads);

        // TODO 如果创建了文件，则删除对应文件

        NotificationPlugin.success({
            title: '删除任务成功',
            placement: 'top-right',
            duration: 3000,
            offset: [-10, 10],
            closeBtn: true,
        });
        if (tempLowThreads.length > 0) {
            if (tempLowThreads[0].id == currentThreadId) {
                setLoading(false);
            } else {
                selectThread(tempLowThreads[0].id);
            }
        } else if (tempTopThreads.length > 0) {
            if (tempTopThreads[0].id == currentThreadId) {
                setLoading(false);
            } else {
                selectThread(tempTopThreads[0].id);
            }
        } else {
            createNewThread(true);
        }
    };

    // 置顶
    const onTopThread = (threadId: string) => {
        console.log("置顶Thread. threadId: ", threadId);
        setLoading(true, "置顶任务中");

        // 从threads中找到threadId对应的thread，删除threads中的thread，并添加到topThreads中
        const threadToTop = threads.find(thread => thread.id === threadId);
        if (threadToTop) {
            // 更新thread的top状态
            const updatedThread = { ...threadToTop, top: true };

            // 从threads中移除
            setThreads(prev => prev.filter(thread => thread.id !== threadId));

            // 添加到topThreads中
            setTopThreads(prev => [updatedThread, ...prev]);
        }

        apiClient.updateLangGraphThread(threadId, {
            metadata: {
                top: true
            }
        }).then(res => {
            console.log("成功置顶Thread. res: ", res);
            NotificationPlugin.success({
                title: '置顶任务成功',
                placement: 'top-right',
                duration: 3000,
                offset: [-10, 10],
                closeBtn: true,
            });
            // 立即刷新状态确保数据同步
            handleRefreshThreadState();
        }).catch(err => {
            console.error("置顶Thread失败. err: ", err);
            NotificationPlugin.error({
                title: '置顶任务失败',
                content: err,
                placement: 'top-right',
                duration: 3000,
                offset: [-10, 10],
                closeBtn: true,
            });
            // 如果API调用失败，回滚状态
            if (threadToTop) {
                setThreads(prev => [...prev, threadToTop]);
                setTopThreads(prev => prev.filter(thread => thread.id !== threadId));
            }
        }).finally(() => {
            setLoading(false);
        })
    }

    // 取消置顶
    const onCancelTopThread = (threadId: string) => {
        console.log("取消置顶Thread. threadId: ", threadId);
        setLoading(true, "取消置顶任务中");

        // 从topThreads中找到threadId对应的thread，删除topThreads中的thread，并添加到threads中
        const threadToUnTop = topThreads.find(thread => thread.id === threadId);
        if (threadToUnTop) {
            // 更新thread的top状态
            const updatedThread = { ...threadToUnTop, top: false };

            // 从topThreads中移除
            setTopThreads(prev => prev.filter(thread => thread.id !== threadId));

            // 添加到threads中
            setThreads(prev => [...prev, updatedThread]);
        }

        apiClient.updateLangGraphThread(threadId, {
            metadata: {
                top: false
            }
        }).then(res => {
            console.log("成功取消置顶Thread. res: ", res);
            NotificationPlugin.success({
                title: '取消置顶任务成功',
                placement: 'top-right',
                duration: 3000,
                offset: [-10, 10],
                closeBtn: true,
            });
            // 立即刷新状态确保数据同步
            handleRefreshThreadState();
        }).catch(err => {
            console.error("取消置顶Thread失败. err: ", err);
            NotificationPlugin.error({
                title: '取消置顶任务失败',
                content: err,
                placement: 'top-right',
                duration: 3000,
                offset: [-10, 10],
                closeBtn: true,
            });
            // 如果API调用失败，回滚状态
            if (threadToUnTop) {
                setTopThreads(prev => [...prev, threadToUnTop]);
                setThreads(prev => prev.filter(thread => thread.id !== threadId));
            }
        }).finally(() => {
            setLoading(false);
        })
    }

    return (
        <Sidebar collapsible="icon" className={`z-90 ${hiddenSidebar ? "hidden!" : ""}`}>
            <SidebarHeader className="p-4 group-data-[collapsible=icon]:p-2 items-center">
                {/* AI Logo 在折叠状态下居中显示 */}
                <div className="flex items-center gap-1 mb-4 group-data-[collapsible=icon]:justify-center group-data-[collapsible=icon]:mb-2">

                    <div className="p-1 rounded-lg group-data-[collapsible=full]:hidden group-data-[collapsible=icon]:show group-data-[collapsible=icon]:p-2">
                        <Image className="" src="/logo.png" alt="logo" width={51.1} height={47} />
                    </div>
                    <div className="group-data-[collapsible=icon]:hidden">
                        <Image className="" src="/sidebar-logo.png" alt="logo" width={226} height={47} />
                    </div>
                </div>

                {/* 新建对话按钮 - 折叠时变成圆形按钮 */}
                <Button
                    onClick={() => createNewThread(false)}
                    className="
                    w-[254px] 
                    h-[54px] 
                    cursor-pointer 
                    group-data-[collapsible=icon]:w-10 
                    group-data-[collapsible=icon]:h-10 
                    group-data-[collapsible=icon]:p-0 
                    group-data-[collapsible=icon]:rounded-sm 
                    group-data-[collapsible=icon]:flex 
                    group-data-[collapsible=icon]:items-center 
                    group-data-[collapsible=icon]:justify-center 
                    bg-white
                    shadow-none
                    hover:bg-white
                    tracking-wide
                    "
                    variant="secondary"
                >
                    <motion.div
                        className="cursor-pointer flex items-center gap-1"
                        variants={buttonVariants}
                        initial="idle"
                        whileHover="hover"
                        whileTap="tap"
                    >
                        <Image className="group-data-[collapsible=icon]:mr-0 group-data-[collapsible=icon]:h-5 group-data-[collapsible=icon]:w-5" src="/创建任务.png" alt="置顶" width={17.86} height={19.29} />
                        <span className="text-base font-semibold text-[#010930] font-stretch-extra-condensed group-data-[collapsible=icon]:hidden">创建任务</span>
                    </motion.div>
                </Button>
            </SidebarHeader>

            <SidebarContent className="overflow-y-auto custom-scrollbar py-2 pl-2 group-data-[collapsible=icon]:p-1">
                <SidebarGroup className="group-data-[collapsible=icon]:p-0">
                    {/* 对话历史标签 - 折叠时隐藏 */}
                    {topThreads.length > 0 ? (
                        <>
                            <SidebarGroupLabel className="flex items-center text-xs gap-2 mb-3 group-data-[collapsible=icon]:hidden">
                                <Image src="/置顶.png" alt="置顶" width={16} height={16} />
                                <span className="text-white/60">置顶</span>
                            </SidebarGroupLabel>

                            <SidebarGroupContent>
                                <div className="space-y-2 group-data-[collapsible=icon]:space-y-1 items-center">
                                    {topThreads.map((topThread) => (
                                        <div
                                            key={'sidebar' + topThread.id}
                                            className={`
                                            cursor-pointer transition-all duration-200 hover:bg-accent/50 rounded-lg p-2
                                            ${currentThreadId === topThread.id
                                                    ? "bg-secondary/10 border-2 border-secondary/20"
                                                    : "hover:bg-white/30 border border-transparent"
                                                }
                                            group-data-[collapsible=icon]:w-10 group-data-[collapsible=icon]:h-10 
                                            group-data-[collapsible=icon]:flex group-data-[collapsible=icon]:items-center 
                                            group-data-[collapsible=icon]:justify-center group-data-[collapsible=icon]:p-0
                                            group-data-[collapsible=icon]:rounded-sm group-data-[collapsible=icon]:mx-auto
                                        `}
                                            onClick={() => {
                                                selectThread(topThread.id)
                                            }}
                                        >
                                            {/* 展开状态下的完整卡片内容 */}
                                            <div className="flex justify-between items-center group-data-[collapsible=icon]:hidden w-full">
                                                <div>
                                                    <div className="flex items-center justify-between mb-1">
                                                        <div className="flex items-center gap-2">
                                                            <span className="text-base font-normal truncate max-w-45 overflow-hidden text-ellipsis whitespace-nowrap tracking-wide">
                                                                {topThread.title}
                                                            </span>
                                                        </div>

                                                        {/* {currentThreadId === thread.id && (
                                                    <Badge variant="secondary" className="text-xs bg-green-100 text-green-700">
                                                        活跃
                                                    </Badge>
                                                )} */}
                                                    </div>
                                                    {/* <div className="flex items-center gap-1 text-xs text-muted-foreground">
                                                    <Clock className="text-white h-3 w-3" />
                                                    <span className="text-white">{formatTime(thread.createdAt)}</span>
                                                </div> */}
                                                    {
                                                        topThread.values == null ? (
                                                            <div className="flex items-center gap-1 text-sm text-[#FFFFFF99] tracking-wide">
                                                                <span>未开始对话</span>
                                                            </div>
                                                        ) : topThread.status == 'idle' ? (
                                                            <div className="flex items-center gap-1 text-sm text-[#FFFFFF99] tracking-wide">
                                                                <span >已执行完毕，可继续对话</span>
                                                            </div>
                                                        ) : topThread.status == 'busy' ? (
                                                            <div className="flex items-center gap-1 text-sm bg-linear-177 from-[#3BFFFE] to-[#4499FF] bg-clip-text text-transparent tracking-wide">
                                                                <Dot className="text-[#3BFFFE] h-6 w-6" />
                                                                <span>进行中</span>
                                                            </div>
                                                        ) : topThread.status == 'interrupted' ? (
                                                            <div className="flex items-center gap-1 text-sm text-[#FFFFFF99] tracking-wide">
                                                                <span>任务中断</span>
                                                            </div>
                                                        ) : (
                                                            <div className="flex items-center gap-1 text-sm text-[#FFFFFF99] tracking-wide">
                                                                <span >任务结束</span>
                                                            </div>
                                                        )
                                                    }
                                                </div>
                                                <DropdownMenu >
                                                    <DropdownMenuTrigger asChild>
                                                        <Button
                                                            className="size-7 outline-none"
                                                            variant="ghost"
                                                            size="icon"
                                                            onClick={(event) => {
                                                                // 阻止事件冒泡到父元素
                                                                event.stopPropagation();
                                                            }}
                                                        >
                                                            <DotsHorizontalIcon className="outline-none" />
                                                        </Button>
                                                    </DropdownMenuTrigger>
                                                    <DropdownMenuContent
                                                        className="z-100 rounded-md bg-gray-100 p-2 shadow-[0px_10px_38px_-10px_rgba(22,_23,_24,_0.35),_0px_10px_20px_-15px_rgba(22,_23,_24,_0.2)]"
                                                        side="bottom"
                                                        sideOffset={5}
                                                        onCloseAutoFocus={(e) => e.preventDefault()}
                                                    >
                                                        <DropdownMenuItem
                                                            className="cursor-pointer flex items-center px-4 py-1 rounded-md select-none leading-none outline-none data-[highlighted]:bg-blue-100 data-[highlighted]:text-blue-500"
                                                            onClick={(event) => {
                                                                // 阻止事件冒泡到父元素
                                                                event.stopPropagation();

                                                                onCancelTopThread(topThread.id)
                                                            }}
                                                        >
                                                            <div className="flex items-center">
                                                                <ArrowDownFromLine className="size-4 mr-2" />
                                                                <span className="text-sm">取消置顶</span>
                                                            </div>
                                                        </DropdownMenuItem>
                                                        <DropdownMenuItem
                                                            className="cursor-pointer flex items-center px-4 py-1 rounded-md select-none leading-none outline-none data-[highlighted]:bg-red-100 data-[highlighted]:text-red-500"
                                                            onClick={(event) => {
                                                                // 阻止事件冒泡到父元素
                                                                event.stopPropagation();
                                                                onDeleteThread(topThread.id)
                                                            }}
                                                        >
                                                            <Trash className="size-4 mr-2" />
                                                            <span className="text-sm">删除</span>
                                                        </DropdownMenuItem>
                                                    </DropdownMenuContent>
                                                </DropdownMenu>
                                            </div>

                                            {/* 折叠状态下只显示图标 */}
                                            <MessageSquare className="h-5 w-5 text-muted-foreground hidden group-data-[collapsible=icon]:block" />
                                        </div>
                                    ))}
                                </div>
                            </SidebarGroupContent>

                            <Separator className="mt-3 mb-3 text-[#cecad5] opacity-20 group-data-[collapsible=icon]:hidden" />
                        </>
                    ) : (<></>)}

                    <div className="flex items-center justify-between group-data-[collapsible=icon]:h-10 group-data-[collapsible=icon]:mb-2 group-data-[collapsible=icon]:justify-center">
                        <SidebarGroupLabel className="flex items-center text-xs gap-2 mb-3 group-data-[collapsible=icon]:hidden">
                            <Image src="/任务.png" alt="任务" width={16} height={16} />
                            <span className="text-white/60">任务</span>
                        </SidebarGroupLabel>
                        <SidebarGroupLabel
                            className="flex items-center text-xs gap-2 mb-3 hover:bg-white/30 cursor-pointer select-none group-data-[collapsible=icon]:m-0 group-data-[collapsible=icon]:opacity-100 group-data-[collapsible=icon]:rounded-full"
                            onClick={() => deleteAllThreads()}
                        >
                            <Image className="group-data-[collapsible=icon]:block" src="/清空.png" alt="清空" width={18} height={18} />
                            <span className="text-white/60 group-data-[collapsible=icon]:hidden">清空</span>
                        </SidebarGroupLabel>
                    </div>


                    <SidebarGroupContent>
                        <div className="space-y-2 group-data-[collapsible=icon]:space-y-1 items-center">
                            {threads.length > 0 ? (
                                threads.map((thread) => (
                                    <div
                                        key={'sidebar' + thread.id}
                                        className={`
                                            transition-all duration-200 hover:bg-accent/50 rounded-lg p-2
                                            ${currentThreadId === thread.id
                                                ? "bg-secondary/10 border-2 border-secondary/20 hover:bg-secondary/10 cursor-default"
                                                : "hover:bg-white/30 border border-transparent cursor-pointer"
                                            }
                                            group-data-[collapsible=icon]:w-10 group-data-[collapsible=icon]:h-10 
                                            group-data-[collapsible=icon]:flex group-data-[collapsible=icon]:items-center 
                                            group-data-[collapsible=icon]:justify-center group-data-[collapsible=icon]:p-0
                                            group-data-[collapsible=icon]:rounded-sm group-data-[collapsible=icon]:mx-auto
                                        `}
                                        onClick={() => {
                                            if (thread.id == currentThreadId) {
                                                return;
                                            }
                                            selectThread(thread.id)
                                        }}
                                    >
                                        {/* 展开状态下的完整卡片内容 */}
                                        <div className="flex justify-between items-center group-data-[collapsible=icon]:hidden w-full">
                                            <div>
                                                <div className="flex items-center justify-between mb-1">
                                                    <div className="flex items-center gap-2">
                                                        <span className="text-base font-normal truncate max-w-45 overflow-hidden text-ellipsis whitespace-nowrap tracking-wide">
                                                            {thread.title}
                                                        </span>
                                                    </div>

                                                    {/* {currentThreadId === thread.id && (
                                                    <Badge variant="secondary" className="text-xs bg-green-100 text-green-700">
                                                        活跃
                                                    </Badge>
                                                )} */}
                                                </div>
                                                {/* <div className="flex items-center gap-1 text-xs text-muted-foreground">
                                                    <Clock className="text-white h-3 w-3" />
                                                    <span className="text-white">{formatTime(thread.createdAt)}</span>
                                                </div> */}

                                                {thread.values == null ? (
                                                    <div className="flex items-center gap-1 text-sm text-[#FFFFFF99] tracking-wide">
                                                        <span>未开始对话</span>
                                                    </div>
                                                ) : thread.status == 'idle' ? (
                                                    <div className="flex items-center gap-1 text-sm text-[#FFFFFF99] tracking-wide">
                                                        <span >已执行完毕，可继续对话</span>
                                                    </div>
                                                ) : thread.status == 'busy' ? (
                                                    <div className="flex items-center gap-1 text-sm bg-linear-177 from-[#3BFFFE] to-[#4499FF] bg-clip-text text-transparent tracking-wide">
                                                        <Dot className="text-[#3BFFFE] h-6 w-6" />
                                                        <span>进行中</span>
                                                    </div>
                                                ) : thread.status == 'interrupted' ? (
                                                    <div className="flex items-center gap-1 text-sm text-[#FFFFFF99] tracking-wide">
                                                        <span>任务中断</span>
                                                    </div>
                                                ) : (
                                                    <div className="flex items-center gap-1 text-sm text-[#FFFFFF99] tracking-wide">
                                                        <span >任务结束</span>
                                                    </div>
                                                )}
                                            </div>
                                            <AnimatePresence>
                                                <DropdownMenu >
                                                    <DropdownMenuTrigger asChild>
                                                        <Button
                                                            className="size-7 outline-none"
                                                            variant="ghost"
                                                            size="icon"
                                                            onClick={(event) => {
                                                                // 阻止事件冒泡到父元素
                                                                event.stopPropagation();
                                                            }}
                                                        >
                                                            <DotsHorizontalIcon className="outline-none" />
                                                        </Button>
                                                    </DropdownMenuTrigger>
                                                    <DropdownMenuContent
                                                        className="z-100 rounded-md bg-gray-100 p-2 shadow-[0px_10px_38px_-10px_rgba(22,_23,_24,_0.35),_0px_10px_20px_-15px_rgba(22,_23,_24,_0.2)]"
                                                        side="bottom"
                                                        sideOffset={5}
                                                        onCloseAutoFocus={(e) => e.preventDefault()}
                                                    >
                                                        <DropdownMenuItem
                                                            className="cursor-pointer flex items-center px-4 py-1 rounded-md select-none leading-none outline-none data-[highlighted]:bg-blue-100 data-[highlighted]:text-blue-500"
                                                            onClick={(event) => {
                                                                // 阻止事件冒泡到父元素
                                                                event.stopPropagation();

                                                                onTopThread(thread.id)
                                                            }}
                                                        >
                                                            <div className="inline-flex">
                                                                <ArrowUpFromLine className="size-4 mr-2" />
                                                                <span className="text-sm">置顶</span>
                                                            </div>
                                                        </DropdownMenuItem>
                                                        <DropdownMenuItem
                                                            className="cursor-pointer flex items-center px-4 py-1 rounded-md select-none leading-none outline-none data-[highlighted]:bg-red-100 data-[highlighted]:text-red-500"
                                                            onClick={(event) => {
                                                                // 阻止事件冒泡到父元素
                                                                event.stopPropagation();
                                                                onDeleteThread(thread.id)
                                                            }}
                                                        >
                                                            <Trash className="size-4 mr-2" />
                                                            <span className="text-sm">删除</span>
                                                        </DropdownMenuItem>
                                                    </DropdownMenuContent>
                                                </DropdownMenu>
                                            </AnimatePresence>
                                        </div>

                                        {/* 折叠状态下只显示图标 */}
                                        <MessageSquare className="h-5 w-5 text-muted-foreground hidden group-data-[collapsible=icon]:block" />
                                    </div>
                                ))
                            ) : (
                                <div className="text-center py-8 group-data-[collapsible=icon]:py-2 group-data-[collapsible=icon]:flex group-data-[collapsible=icon]:justify-center">
                                    <div className="group-data-[collapsible=icon]:hidden">
                                        <MessageSquare className="h-12 w-12 mx-auto mb-4 text-muted-foreground/50" />
                                        <h3 className="font-medium mb-2">暂无对话历史</h3>
                                        <p className="text-sm text-muted-foreground">
                                            点击上方按钮开始新的对话
                                        </p>
                                    </div>
                                    {/* 折叠状态下显示简化的图标 */}
                                    <MessageSquare className="h-6 w-6 text-muted-foreground/50 hidden group-data-[collapsible=icon]:block" />
                                </div>
                            )}
                        </div>
                    </SidebarGroupContent>
                </SidebarGroup>
            </SidebarContent>

            <SidebarFooter className="p-4 group-data-[collapsible=icon]:p-2">
                <div className="flex justify-end w-full group-data-[collapsible=icon]:justify-center">
                    <SidebarTrigger variant="secondary" className="cursor-pointer group-data-[collapsible=icon]:size-10" />
                </div>
            </SidebarFooter>
        </Sidebar >
    )
}
