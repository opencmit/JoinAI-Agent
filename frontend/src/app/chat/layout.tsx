import "@noahlocal/copilotkit-react-ui/styles.css";
import "@/app/globals.css";

import { Suspense } from "react";

import { GlobalLoading } from "@/components/ui/global-loading";

import { AppSidebar } from "@/app/ui/app-sidebar"
import { LoadingProvider } from "@/lib/loading-context";
import { ModeProvider } from "@/lib/mode-context";
import { MessageProvider } from "@/lib/message-context";
import { AttachmentProvider } from "@/lib/attachment-context";


export default async function ChatLayout({
    children
}: Readonly<{
    children: React.ReactNode;
}>) {
    console.log('加载chat layout')

    return (
        <div className="flex flex-row h-full w-full overflow-y-hidden bg-[url(/chat-background.png)] bg-no-repeat bg-center bg-cover">
            <LoadingProvider>
                <GlobalLoading />
                <AttachmentProvider>
                    <Suspense>
                        <AppSidebar />
                    </Suspense>
                    <ModeProvider>
                        <MessageProvider>
                            {children}
                        </MessageProvider>
                    </ModeProvider>
                </AttachmentProvider>
            </LoadingProvider>
        </div>
    );
}
