"use client";

import React, { memo, useCallback, useEffect, useRef, useState } from 'react';
import Image from 'next/image';
import { ChevronLeft, ChevronRight, KeyboardIcon, MousePointer2Icon, ScrollIcon, CheckIcon } from 'lucide-react';
import { motion } from "framer-motion";

import { BrowserUseStepItem, BrowserUseSteps } from '@/types/browser-use';

import { Button } from "@/components/ui/button";
import { SwitchIcon } from '@radix-ui/react-icons';

// 缩略图组件
const ThumbnailImage = memo<{ step: BrowserUseStepItem, isActive: boolean, index: number, onThumbnailClick: (index: number) => void }>(function ThumbnailImage({ step, isActive, index, onThumbnailClick }: { step: BrowserUseStepItem, isActive: boolean, index: number, onThumbnailClick: (index: number) => void }) {
    const handleClick = useCallback(() => {
        onThumbnailClick(index);
    }, [index, onThumbnailClick]);

    return (
        <motion.button
            onClick={handleClick}
            variants={{
                idle: { scale: 1 },
                hover: { scale: 1.05 },
                tap: { scale: 0.95 },
            }}
            initial="idle"
            whileHover="hover"
            whileTap="tap"
            className={`flex-none relative flex flex-col px-2 py-1 items-center justify-center rounded-md overflow-hidden border-2 transition-all duration-200 cursor-pointer bg-transparent ${isActive ? 'outline-2 outline-blue-500' : 'border-zinc-200 dark:border-zinc-700'
                }`}
        >
            <div className="flex flex-row gap-2 items-center justify-center">
                <Image
                    src={step.screenshot_url}
                    alt="缩略图"
                    width={32}
                    height={32}
                    className="w-14 h-14 object-cover rounded-md"
                    unoptimized
                />
                <div className="flex flex-col gap-1 items-center justify-center text-xs">
                    {step.actions.length > 0 && step.actions.map((action, index) => {
                        if ('input' in action) {
                            return (
                                <div key={index} className="flex flex-row items-center justify-center gap-1 bg-blue-500/10 text-blue-500 rounded-md px-2 py-1">
                                    <KeyboardIcon className="w-4 h-4" />
                                    input
                                </div>
                            )
                        }
                        if ('click' in action) {
                            return (
                                <div key={index} className="flex flex-row items-center justify-center gap-1 bg-green-500/10 text-green-500 rounded-md px-2 py-1">
                                    <MousePointer2Icon className="w-4 h-4" />
                                    click
                                </div>
                            )
                        }
                        if ('scroll' in action) {
                            return (
                                <div key={index} className="flex flex-row items-center justify-center gap-1 bg-yellow-500/10 text-yellow-500 rounded-md px-2 py-1">
                                    <ScrollIcon className="w-4 h-4" />
                                    scroll
                                </div>
                            )
                        }
                        if ('done' in action) {
                            return (
                                <div key={index} className="flex flex-row items-center justify-center gap-1 bg-red-500/10 text-red-500 rounded-md px-2 py-1">
                                    <CheckIcon className="w-4 h-4" />
                                    done
                                </div>
                            )
                        }
                        if ('switch' in action) {
                            return (
                                <div key={index} className="flex flex-row items-center justify-center gap-1 bg-purple-500/10 text-purple-500 rounded-md px-2 py-1">
                                    <SwitchIcon className="w-4 h-4" />
                                    switch
                                </div>
                            )
                        }
                        return null;
                    })}
                </div>
            </div>
            <div className="w-32 text-xs text-zinc-500 dark:text-zinc-400 truncate">
                {step.memory}
            </div>
        </motion.button>
    );
});

interface BrowserUseTaskProps {
    steps?: BrowserUseSteps; // 报告正文内容（流式输出）
    sandboxId?: string; // 沙箱ID，用于下载文件
}

export const BrowserUseTask = memo(function BrowserUseTask({
    steps = {
        total_steps: 0,
        steps: [],
        is_success: false,
    }
}: BrowserUseTaskProps) {
    const [currentStepIndex, setCurrentStepIndex] = useState<number>(0);
    const thumbnailsContainerRef = useRef<HTMLDivElement | null>(null);

    const handleClickImage = useCallback((index: number) => {
        // console.log("handleClickImage", image);
        setCurrentStepIndex(index);
    }, [setCurrentStepIndex]);

    const handlePreviousImage = () => {
        const newIndex = currentStepIndex > 0 ? currentStepIndex - 1 : steps.total_steps - 1;
        // setCurrentImageIndex(newIndex);
        handleClickImage(newIndex);
    };

    const handleNextImage = () => {
        const newIndex = currentStepIndex < steps.total_steps - 1 ? currentStepIndex + 1 : 0;
        // setCurrentImageIndex(newIndex);
        handleClickImage(newIndex);
    };

    // 当前选中的缩略图滚动到中间（仅在出现水平滚动条时）
    useEffect(() => {
        const container = thumbnailsContainerRef.current;
        if (!container) return;

        // 没有水平滚动条时不处理
        if (container.scrollWidth <= container.clientWidth) return;

        const activeChild = container.children[currentStepIndex] as HTMLElement | undefined;
        if (!activeChild || typeof activeChild.scrollIntoView !== 'function') return;

        // 使用浏览器原生 scrollIntoView，让当前元素在容器中水平居中
        activeChild.scrollIntoView({
            behavior: 'smooth',
            block: 'nearest',
            inline: 'center',
        });
    }, [currentStepIndex, steps.steps.length]);

    return (
        <div className="flex flex-col h-full w-full">
            {/* 截图 */}
            <div className="grow w-full p-4 space-y-4">
                {steps.steps[currentStepIndex].screenshot_url ? (<Image
                    src={steps.steps[currentStepIndex].screenshot_url}
                    alt="缩略图"
                    width={32}
                    height={32}
                    className="w-full h-full object-cover"
                    unoptimized
                />
                ) : (
                    <div className="w-full flex items-center justify-center">
                        无截图
                    </div>
                )}
            </div>

            {/* 底部缩略图步骤 */}
            <div className="flex items-center justify-center gap-2 px-4 bg-transparent border-t border-zinc-200/50">
                {/* 左箭头 */}
                {steps.total_steps > 1 && (
                    <Button
                        variant="outline"
                        size="icon"
                        onClick={handlePreviousImage}
                        className="w-8 h-8 rounded-full hover:bg-primary/10 hover:text-primary transition-colors"
                    >
                        <ChevronLeft className="w-4 h-4" />
                    </Button>
                )}

                {/* 缩略图列表 */}
                <div
                    ref={thumbnailsContainerRef}
                    className="flex items-center gap-2 p-2 max-w-md overflow-x-auto custom-scrollbar"
                >
                    {steps.steps.map((step, index) => (
                        <ThumbnailImage
                            key={step.step_number}
                            step={step}
                            isActive={index === currentStepIndex}
                            index={index}
                            onThumbnailClick={handleClickImage}
                        />
                    ))}
                </div>

                {/* 右箭头 */}
                {steps.total_steps > 1 && (
                    <Button
                        variant="outline"
                        size="icon"
                        onClick={handleNextImage}
                        className="w-8 h-8 rounded-full hover:bg-primary/10 hover:text-primary transition-colors"
                    >
                        <ChevronRight className="w-4 h-4" />
                    </Button>
                )}
            </div>
        </div>
    );
});

