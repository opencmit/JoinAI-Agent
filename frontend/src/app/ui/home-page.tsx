"use client"

import "tdesign-react/es/_util/react-19-adapter";
import Image from 'next/image'
import { useEffect, useState } from "react";
import { motion, AnimatePresence, easeOut } from "motion/react";
import { useRouter } from "next/navigation";
import { NotificationPlugin } from 'tdesign-react';
import { useModeContext } from "@/lib/mode-context";
import { useMessageContext } from "@/lib/message-context";
import { useLoading } from "@/lib/loading-context";
import { apiClient } from "@/lib/api-client";
import { useAttachmentContext } from "@/lib/attachment-context";
import { FileUploader } from "@/app/ui/file-uploader";
import { Button } from "@/components/ui/button";
import { useSidebar } from "@/components/ui/sidebar";
import {
    buttonVariants,
} from "@/lib/animations";

export function HomePage({ threadId }: { threadId: string }) {
    const { setLoading } = useLoading() // 使用loading-context
    const [inputValue, setInputValue] = useState("");
    const router = useRouter();

    const { attachmentList } = useAttachmentContext();
    const { mode } = useModeContext();
    const { setTitle } = useSidebar();

    const { setMessage } = useMessageContext();

    useEffect(() => {
        setLoading(false);
    }, [threadId])

    const send = async (message: string) => {
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

        setLoading(true, "对话初始化中");

        const files: string[] = [];

        // 这里可以添加逻辑来处理选中的工具
        console.log("发送消息:", message);
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

        setMessage(
            message,
            mode,
            "normal",
            files
        );

        // 调用模型获取对话标题
        generateTitle(message);

        router.replace(`/chat?threadId=${threadId}&init=true`);
    }

    async function generateTitle(message: string) {
        console.log("开始生成标题", message)
        const title = await apiClient.getThreadTitle(message);
        if (title.success) {
            if (title.title.length > message.length) {
                setTitle(message);
            } else {
                setTitle(title.title);
            }
        } else {
            setTitle(message);
        }

        apiClient.updateLangGraphThread(threadId, {
            metadata: {
                title: title.title
            }
        })
        console.log("生成标题完成", title)
    }

    const handleKeyDown = async (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            send(inputValue);
        }
    };

    const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
        setInputValue(e.target.value);
    }

    return (
        <div className="overflow-y-auto">
            <AnimatePresence>
                <motion.div
                    className="flex flex-col items-center justify-center h-[78vh] p-4"
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 1.05 }}
                    transition={{ duration: 0.4, ease: easeOut }}
                >
                    <div className="w-4xl relative flex flex-col items-start justify-between mb-10">
                        {(() => {
                            const hour = new Date().getHours();
                            if (hour >= 5 && hour < 11) {
                                return <Image
                                    className="overflow-visible absolute -top-5 right-0"
                                    src="/bg-morning.png"
                                    alt="Hello"
                                    width={140}
                                    height={140}
                                />;
                            } else if (hour >= 11 && hour < 14) {
                                return <Image
                                    className="overflow-visible absolute -top-5 right-0"
                                    src="/bg-afternoon-1.png"
                                    alt="Hello"
                                    width={140}
                                    height={140}
                                />;
                            } else if (hour >= 14 && hour < 18) {
                                return <Image
                                    className="overflow-visible absolute -top-5 right-0"
                                    src="/bg-afternoon-2.png"
                                    alt="Hello"
                                    width={140}
                                    height={140}
                                />;
                            } else if (hour >= 18 && hour < 24) {
                                return <Image
                                    className="overflow-visible absolute -top-5 right-0"
                                    src="/bg-night.png"
                                    alt="Hello"
                                    width={140}
                                    height={140}
                                />;
                            } else if (hour >= 0 && hour < 5) {
                                return <Image
                                    className="overflow-visible absolute -top-5 right-0"
                                    src="/bg-deepnight.png"
                                    alt="Hello"
                                    width={140}
                                    height={140}
                                />;
                            }
                        })()}
                        <div
                            className="font-[PingFang_SC] text-center md:text-left ml-15"
                        >
                            <h1 className="italic text-4xl/12 font-bold text-[#363B64]/80 tracking-widest">
                                {(() => {
                                    const hour = new Date().getHours();
                                    if (hour >= 5 && hour < 9) {
                                        return "早安！我的朋友~";
                                    } else if (hour >= 9 && hour < 12) {
                                        return "上午好呀！我的朋友~";
                                    } else if (hour >= 12 && hour < 14) {
                                        return "中午好呀！我的朋友~";
                                    } else if (hour >= 14 && hour < 18) {
                                        return "下午好呀！我的朋友~";
                                    } else if (hour >= 18 && hour < 24) {
                                        return "晚上好呀！我的朋友~";
                                    } else if (hour >= 0 && hour < 5) {
                                        return "夜深了！我的朋友~";
                                    } else {
                                        return "你好呀！我的朋友~";
                                    }
                                })()}
                            </h1>
                            <p className="text-xl text-[#363B64]/70 mt-2 tracking-widest">
                                {(() => {
                                    const hour = new Date().getHours();
                                    if (hour >= 5 && hour < 9) {
                                        return "新的一天充满无限可能~";
                                    } else if (hour >= 9 && hour < 12) {
                                        return "让我们一起创造精彩~";
                                    } else if (hour >= 12 && hour < 14) {
                                        return "我能为你做点什么呢？";
                                    } else if (hour >= 14 && hour < 18) {
                                        return "继续加油，胜利在望~";
                                    } else if (hour >= 18 && hour < 24) {
                                        return "今天又进步了一点~";
                                    } else if (hour >= 0 && hour < 5) {
                                        return "明天会更好~";
                                    } else {
                                        return "我能为你做点什么呢？";
                                    }
                                })()}
                            </p>
                        </div>
                    </div>

                    {/* 新增的容器 div，包含顶部文字、搜索框和功能卡片 */}
                    <div className="w-4xl relative box-border rounded-2xl border-1 border-transparent bg-linear-to-b/oklch from-yellow-400 to-purple-400 bg-clip-border bg-origin-border">
                        <div className="relative box-border z-10 rounded-2xl bg-white">
                            <div className="relative box-border z-10 rounded-2xl bg-white/60 backdrop-blur-xl p-3">
                                <div className="relative flex">
                                    <textarea
                                        value={inputValue}
                                        onChange={handleInputChange}
                                        onKeyDown={handleKeyDown}
                                        placeholder="请在此输入您的问题，按回车键发送"
                                        className="w-full border-0 bg-transparent text-base/6 font-[PingFang_SC] tracking-widest placeholder:text-gray-400 focus-visible:ring-0 resize-none outline-none px-4 py-2"
                                        style={{ textIndent: "0em" }}
                                        rows={3}
                                    />
                                </div>

                                <div className="flex items-center justify-between pt-3 mt-2 pl-4">
                                    <div className="flex items-center gap-1">
                                        <FileUploader key={threadId} disabled={false} threadId={threadId} />
                                    </div>
                                    <div className="flex flex-row items-center text-center justify-center gap-1">
                                        <Button
                                            asChild
                                            variant="outline"
                                            className="w-20 rounded-sm border-none hover:bg-transparent text-sm shadow-none"
                                            size="icon"
                                            onClick={() => send(inputValue)}
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
                    </div>
                </motion.div>
            </AnimatePresence>
        </div>
    )
}
