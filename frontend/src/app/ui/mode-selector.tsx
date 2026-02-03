"use client";

import { Button } from "@/components/ui/button";
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuPortal, DropdownMenuContent, DropdownMenuRadioGroup, DropdownMenuRadioItem } from "@/components/ui/dropdown-menu";
import Image from 'next/image'

import {
    BadgeEuro,
    BadgeHelp
} from "lucide-react";
import { useModeContext } from "@/lib/mode-context";

export function ModeSelector() {
    const { mode, setMode } = useModeContext();
    return (
        <div className="w-30 max-w-xs z-10">
            <DropdownMenu>
                <DropdownMenuTrigger asChild>
                    <Button
                        asChild
                        variant="outline"
                        className="h-9 px-5! rounded-full border-gray-300 hover:bg-gray-100 text-sm shadow-none"
                    >
                        <div>
                            <Image
                                width="24"
                                height="24"
                                src="/mode-selector.png"
                                alt="mode-selector"
                            />
                            <span className="font-[PingFang_SC] font-normal text-[#363B64]">模式</span>
                        </div>
                    </Button>
                </DropdownMenuTrigger>
                <DropdownMenuPortal>
                    <DropdownMenuContent
                        className="rounded-md p-2 bg-white shadow-[0px_10px_38px_-10px_rgba(22,_23,_24,_0.35),_0px_10px_20px_-15px_rgba(22,_23,_24,_0.2)]"
                        onCloseAutoFocus={(e) => e.preventDefault()}
                    >
                        <DropdownMenuRadioGroup value={mode} onValueChange={setMode} className="flex flex-col gap-2">
                            {/* <DropdownMenuRadioItem disabled className="flex rounded-lg justify-between items-center p-2 select-none leading-none outline-none data-[highlighted]:bg-blue-100 data-[highlighted]:text-blue-500" value="auto">
                                <div className="flex items-center mr-10">
                                    <BadgeDollarSign />
                                    <div className="flex flex-col ml-2">
                                        <span className="text-base">自动模式</span>
                                        <span className="text-xs">让AI自主决策需使用探索&规划模式</span>
                                    </div>
                                </div>
                            </DropdownMenuRadioItem> */}
                            <DropdownMenuRadioItem disabled className="flex rounded-lg justify-between items-center p-2 select-none leading-none outline-none data-[highlighted]:bg-blue-100 data-[highlighted]:text-blue-500" value="plan">
                                <div className="flex items-center mr-10">
                                    <BadgeEuro />
                                    <div className="flex flex-col ml-2">
                                        <span className="text-base">规划模式</span>
                                        <span className="text-xs">AI帮助你规划步骤，分步帮你执行</span>
                                    </div>
                                </div>
                            </DropdownMenuRadioItem>
                            <DropdownMenuRadioItem className="flex rounded-lg justify-between items-center p-2 select-none leading-none outline-none data-[highlighted]:bg-blue-100 data-[highlighted]:text-blue-500" value="explore">
                                <div className="flex items-center mr-10">
                                    <BadgeHelp />
                                    <div className="flex flex-col ml-2">
                                        <span className="text-base">探索模式</span>
                                        <span className="text-xs">让AI自主动态思考，完成速度更快</span>
                                    </div>
                                </div>
                            </DropdownMenuRadioItem>
                        </DropdownMenuRadioGroup>
                    </DropdownMenuContent>
                </DropdownMenuPortal>
            </DropdownMenu>
        </div>
    );
}