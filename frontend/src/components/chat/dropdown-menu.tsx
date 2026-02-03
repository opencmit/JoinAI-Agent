import { Button } from "@/components/ui/button"
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuPortal,
    DropdownMenuSub,
    DropdownMenuSubContent,
    DropdownMenuSubTrigger,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { MoreHorizontal } from "lucide-react"
import { UsageMetadata } from "@/types/agent";

interface DropdownMenuComponentProps {
    usageMetadata?: UsageMetadata | null;
}

export function DropdownMenuComponent({ usageMetadata }: DropdownMenuComponentProps) {
    const completionTokens = (usageMetadata?.output_tokens || 0);
    const tokensPerSecond =
        (usageMetadata?.total_response_time && usageMetadata.total_response_time > 0 && completionTokens > 0)
            ? (completionTokens / (usageMetadata.total_response_time / 1000)).toFixed(2)
            : 'N/A';

    return (
        <div className="flex justify-between">
            {/* <div /> */}
            <DropdownMenu>
                <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="icon">
                        <MoreHorizontal className="h-4 w-4" />
                    </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent className="" align="start">
                    {/* <DropdownMenuSeparator /> */}
                    <>
                        <DropdownMenuSub>
                            <DropdownMenuSubTrigger>使用统计</DropdownMenuSubTrigger>
                            <DropdownMenuPortal>
                                <DropdownMenuSubContent>
                                    <DropdownMenuItem className="flex justify-between">
                                        <span>首字延迟:</span>
                                        <span>{usageMetadata?.time_to_first_token !== undefined ? `${(usageMetadata.time_to_first_token / 1000).toFixed(2)}s` : 'N/A'}</span>
                                    </DropdownMenuItem>
                                    <DropdownMenuItem className="flex justify-between">
                                        <span>总耗时:</span>
                                        <span>{usageMetadata?.total_response_time !== undefined ? `${(usageMetadata.total_response_time / 1000).toFixed(2)}s` : 'N/A'}</span>
                                    </DropdownMenuItem>
                                    <DropdownMenuItem className="flex justify-between">
                                        <span>生成耗时:</span>
                                        <span>{usageMetadata?.generation_time !== undefined ? `${(usageMetadata.generation_time / 1000).toFixed(2)}s` : 'N/A'}</span>
                                    </DropdownMenuItem>
                                    {/* Prompt tokens */}
                                    <DropdownMenuItem className="flex justify-between">
                                        <span>输入tokens:</span>
                                        <span>{usageMetadata?.input_tokens !== undefined ? usageMetadata.input_tokens : 'N/A'}</span>
                                    </DropdownMenuItem>
                                    {/* Completion tokens */}
                                    <DropdownMenuItem className="flex justify-between">
                                        <span>输出tokens:</span>
                                        <span>{usageMetadata?.output_tokens !== undefined ? usageMetadata.output_tokens : 'N/A'}</span>
                                    </DropdownMenuItem>
                                    <DropdownMenuItem className="flex justify-between">
                                        <span>总tokens:</span>
                                        <span>{usageMetadata?.total_tokens !== undefined ? usageMetadata.total_tokens : 'N/A'}</span>
                                    </DropdownMenuItem>
                                    <DropdownMenuItem className="flex justify-between">
                                        <span>每秒tokens:</span>
                                        <span>{tokensPerSecond}</span>
                                    </DropdownMenuItem>
                                </DropdownMenuSubContent>
                            </DropdownMenuPortal>
                        </DropdownMenuSub>
                    </>
                    {/* <DropdownMenuSeparator /> */}
                </DropdownMenuContent>
            </DropdownMenu>
        </div>
    )
}
