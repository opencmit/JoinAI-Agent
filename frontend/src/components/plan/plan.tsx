"use client";

import Image from 'next/image'
import { useAgentContext } from "@/lib/agent-context";

export function PlanView() {
    const { agentState } = useAgentContext();
    if (!agentState.plan) {
        return null;
    }
    return (
        <div className="w-full h-full flex flex-col rounded-lg p-2 bg-[url(/工作台背景.png)] bg-cover bg-top bg-transparent">
            {/* 顶部title */}
            <div className="w-full flex-none flex flex-row items-center justify-between p-4">
                <div className="font-[PingFang_SC] font-bold flex flex-row items-center gap-2 ">
                    <Image
                        className="transition-all duration-200"
                        width="25"
                        height="25"
                        src="/工作台icon.png"
                        alt="Send"
                    />
                    规划
                </div>
            </div>

            {/* 规划标题 */}
            <div className="w-full flex-none flex flex-row items-center justify-between p-4">
                <div className="font-[PingFang_SC] font-bold flex flex-row items-center gap-2">
                    {agentState.plan.title || "无标题"}
                </div>
            </div>

            {/* 规划步骤 */}
            <div className="w-full flex-1 flex flex-col items-start gap-3 p-4 overflow-y-auto">
                {agentState.plan.steps && agentState.plan.steps.map((step, index) => {
                    const current_plan_step = agentState.current_plan_step;
                    // 判断步骤状态
                    // 当 current_plan_step 为 -1 时，表示全部完成
                    const isAllCompleted = current_plan_step === -1;
                    const isCompleted = isAllCompleted || step.step_index < current_plan_step;
                    const isCurrent = !isAllCompleted && step.step_index === current_plan_step;
                    // const isPending = step.step_index > current_plan_step;

                    return (
                        <div
                            key={index}
                            className="w-full relative group"
                        >
                            {/* 连接线（除最后一个步骤外） */}
                            {index < agentState.plan.steps.length - 1 && (
                                <div className={`absolute left-5 top-12 w-0.5 h-full z-0 ${isCompleted
                                    ? 'bg-gradient-to-b from-[#10B981]/60 via-[#34D399]/40 to-transparent'
                                    : isCurrent
                                        ? 'bg-gradient-to-b from-[#5991FF]/60 via-[#73AAFF]/50 to-transparent'
                                        : 'bg-gradient-to-b from-[#5991FF]/20 via-[#73AAFF]/15 to-transparent'
                                    }`} />
                            )}

                            {/* 卡片内容 */}
                            <div className={`relative flex flex-row items-start gap-4 p-4 rounded-lg bg-[url(/工作台卡片.png)] bg-cover bg-center backdrop-blur-sm border shadow-sm transition-all duration-300 ${isCurrent
                                ? 'border-[#5991FF]/60 shadow-lg shadow-[#5991FF]/20 scale-[1.02] ring-2 ring-[#5991FF]/30'
                                : isCompleted
                                    ? 'border-green-400/40 shadow-md hover:shadow-lg hover:border-green-400/50 hover:scale-[1.01] opacity-90'
                                    : 'border-white/20 hover:shadow-md hover:border-white/30 hover:scale-[1.01] opacity-70'
                                }`}>
                                {/* 序号圆圈 */}
                                <div className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center text-white font-bold text-sm font-[PingFang_SC] shadow-md z-10 transition-all duration-300 ${isCurrent
                                    ? 'bg-gradient-to-br from-[#5991FF] via-[#73AAFF] to-[#AFD4FF] animate-pulse'
                                    : isCompleted
                                        ? 'bg-gradient-to-br from-[#10B981] via-[#34D399] to-[#6EE7B7]'
                                        : 'bg-gradient-to-br from-[#9CA3AF] via-[#D1D5DB] to-[#E5E7EB]'
                                    }`}>
                                    {isCompleted ? (
                                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                                        </svg>
                                    ) : (
                                        <span>{index + 1}</span>
                                    )}
                                </div>

                                {/* 内容区域 */}
                                <div className="flex-1 flex flex-col gap-2 min-w-0">
                                    {/* 智能体名称 */}
                                    <div className={`font-[PingFang_SC] font-bold text-base flex items-center gap-2 ${isCurrent
                                        ? 'text-gray-900'
                                        : isCompleted
                                            ? 'text-gray-700'
                                            : 'text-gray-500'
                                        }`}>
                                        <span className={`flex-none ${isCurrent
                                            ? 'text-[#5991FF]'
                                            : isCompleted
                                                ? 'text-[#10B981]'
                                                : 'text-gray-400'
                                            }`}>智能体:</span>
                                        <span className="truncate">{step.agent_name}</span>
                                        {isCurrent && (
                                            <span className="flex-none ml-auto flex items-center gap-1 text-xs text-[#5991FF] font-normal">
                                                <span className="w-2 h-2 rounded-full bg-[#5991FF] animate-pulse"></span>
                                                执行中
                                            </span>
                                        )}
                                    </div>

                                    {/* 描述 */}
                                    <div className={`font-[PingFang_SC] text-sm leading-relaxed flex-1 ${isCurrent
                                        ? 'text-gray-800'
                                        : isCompleted
                                            ? 'text-gray-600'
                                            : 'text-gray-400'
                                        }`}>
                                        {step.description}
                                    </div>

                                    {/* 备注（如果有） */}
                                    {step.note && (
                                        <div className={`font-[PingFang_SC] text-xs italic mt-1 pl-4 border-l-2 ${isCurrent
                                            ? 'text-gray-600 border-[#5991FF]/40'
                                            : isCompleted
                                                ? 'text-gray-500 border-green-300/40'
                                                : 'text-gray-400 border-gray-300/40'
                                            }`}>
                                            {step.note}
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    )
}
