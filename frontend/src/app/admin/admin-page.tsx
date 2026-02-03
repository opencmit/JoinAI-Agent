"use client"

import Image from 'next/image';
import { AdminAssistantListComponent } from "@/components/admin/assistant-list";
import { AdminThreadListComponent } from "@/components/admin/thread-list";
import { AdminRunListComponent } from "@/components/admin/run-list";
import { AdminStoreListComponent } from "@/components/admin/store-list";
import { useState } from 'react';

export default function AdminPage() {
    const [activeTab, setActiveTab] = useState<string>("assistant");
    const [runListParams, setRunListParams] = useState<{ threadId?: string }>({});
    const [threadListParams, setThreadListParams] = useState<{ assistantId?: string }>({});

    const handleSwitchToThread = (assistantId: string) => {
        setThreadListParams({ assistantId });
        setActiveTab("thread");
    };

    const handleSwitchToRun = (threadId: string) => {
        setRunListParams({ threadId });
        setActiveTab("run");
    };

    const handleSwitchTab = (tab: string) => {
        setThreadListParams({});
        setRunListParams({});
        setActiveTab(tab);
    };

    return (
        <div className="w-full h-screen overflow-hidden flex flex-row">
            {/* 左侧菜单 */}
            <div className="w-50 h-full flex flex-col p-4 overflow-hidden bg-[#010930]">
                {/* Logo */}
                <div className="flex items-center gap-1 mb-4">
                    <div className="p-1 rounded-lg">
                        <Image className="" src="/sidebar-logo.png" alt="logo" width={226} height={47} />
                    </div>
                </div>

                {/* <Separator className="mt-2 mb-6" /> */}

                {/* 菜单 */}
                <div className="flex flex-col gap-2 pt-6">
                    <div
                        onClick={() => handleSwitchTab("assistant")}
                        className={`cursor-pointer text-white py-2 px-4 font-normal text-base hover:bg-white/20 rounded-md ${activeTab === "assistant" ? "bg-white/10" : ""}`}
                    >
                        Assistant管理
                    </div>
                    <div
                        onClick={() => handleSwitchTab("thread")}
                        className={`cursor-pointer text-white py-2 px-4 font-normal text-base hover:bg-white/20 rounded-md ${activeTab === "thread" ? "bg-white/10" : ""}`}
                    >
                        Thread管理
                    </div>
                    <div
                        onClick={() => handleSwitchTab("run")}
                        className={`cursor-pointer text-white py-2 px-4 font-normal text-base hover:bg-white/20 rounded-md ${activeTab === "run" ? "bg-white/10" : ""}`}
                    >
                        Run管理
                    </div>
                    <div
                        onClick={() => handleSwitchTab("store")}
                        className={`cursor-pointer text-white py-2 px-4 font-normal text-base hover:bg-white/20 rounded-md ${activeTab === "store" ? "bg-white/10" : ""}`}
                    >
                        Store管理
                    </div>
                </div>
            </div>

            {/* 右侧内容 */}
            <div className="flex-1 h-screen overflow-hidden">
                {activeTab === "assistant" && <AdminAssistantListComponent onSwitchToThread={handleSwitchToThread} />}
                {activeTab === "thread" && <AdminThreadListComponent onSwitchToRun={handleSwitchToRun} initialAssistantId={threadListParams.assistantId} />}
                {activeTab === "run" && <AdminRunListComponent initialThreadId={runListParams.threadId} />}
                {activeTab === "store" && <AdminStoreListComponent />}
            </div>
        </div>
    );
}
