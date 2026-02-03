"use client"
import { getVNCUrl } from "@/lib/sandbox_manager";
import { useEffect, useState } from "react";
import { AspectRatio } from "@/components/ui/aspect-ratio"
import { useSandboxContext } from "@/lib/agent-context";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"

export function SandboxView() {
    // 使用 context 获取 sandbox id
    const { sandboxId } = useSandboxContext();

    const [vncUrl, setVncUrl] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const fetchVncUrl = async () => {
            if (sandboxId) {
                setIsLoading(true);
                let url = await getVNCUrl(sandboxId);
                console.log("vnc url", url)
                url = url?.replace("https", "http") || "";
                url = `/vnc/${url?.split("/")[3] || ""}`
                console.log("沙盒URL: ", url);

                setVncUrl(url);
                setIsLoading(false);
            } else {
                setVncUrl(null);
                setIsLoading(false);
            }
        };

        fetchVncUrl();
    }, [sandboxId]);

    return (
        <div className="w-full h-full flex flex-col justify-between">
            <div />
            {isLoading ? (
                <div className="flex items-center justify-center w-full h-full">
                    正在加载沙盒环境...
                </div>
            ) : vncUrl ? (
                <AspectRatio ratio={4 / 3} className="bg-muted border rounded-lg shadow-lg p-4">
                    <iframe
                        src={vncUrl}
                        className="w-full h-full"
                        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                        allowFullScreen
                    />
                </AspectRatio>
            ) : (
                <Alert variant="default" className="w-fit mx-auto">
                    <AlertTitle>未使用沙盒环境</AlertTitle>
                    <AlertDescription>
                        发起沙盒操作后，才能看到沙盒环境。
                    </AlertDescription>
                </Alert>
            )}
            <div />
        </div>
    );
}