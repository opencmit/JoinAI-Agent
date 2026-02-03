"use client"

import * as React from "react";
import * as ToastPrimitive from "@radix-ui/react-toast";
import { X } from "lucide-react";
import { Button } from "@/components/ui/button";

const ToastContext = React.createContext<{
    show: (message: string, type: "success" | "error" | "warning" | "info", description?: string) => void;
} | null>(null);

export function ToastProvider({ children }: { children: React.ReactNode }) {
    const [toasts, setToasts] = React.useState<{
        id: number;
        message: string;
        type: "success" | "error" | "warning" | "info";
        description?: string;
    }[]>([]);
    const toastId = React.useRef(0);
    const lastToast = React.useRef<{ msg: string, time: number } | null>(null);
    const show = (msg: string, type: "success" | "error" | "warning" | "info", description?: string) => {
        const now = Date.now();
        if (lastToast.current && lastToast.current.msg === msg && now - lastToast.current.time < 1000) {
            return; // 1秒内同内容不弹
        }
        lastToast.current = { msg, time: now };
        const id = toastId.current++;
        setToasts((prev) => [...prev, { id, message: msg, type, description }]);
        // 自动关闭
        setTimeout(() => {
            setToasts((prev) => prev.filter((t) => t.id !== id));
        }, 2500);
    };

    const handleClose = (id: number) => {
        setToasts((prev) => prev.filter((t) => t.id !== id));
    };

    return (
        <ToastContext.Provider value={{ show }}>
            {children}
            <ToastPrimitive.Provider swipeDirection="right">
                <ToastPrimitive.Viewport
                    className="fixed top-0 right-0 z-[2147483647] m-0 flex w-[390px] max-w-[100vw] list-none flex-col gap-2.5 p-[var(--viewport-padding)] outline-none [--viewport-padding:_25px]"
                // className="fixed top-0 left-1/2 z-[2147483647] m-0 flex w-[390px] max-w-[100vw] list-none flex-col gap-2.5 p-[var(--viewport-padding)] outline-none [--viewport-padding:_25px] -translate-x-1/2 items-center"
                />
                {toasts.map(({ id, message, type, description }) => (
                    <ToastPrimitive.Root
                        key={id}
                        open={true}
                        duration={2500}
                        className={`
                            z-99999
                            items-center 
                            rounded-md 
                            shadow-md
                            text-black
                            bg-white
                            border-l-6
                            ${type === "success" ? "border-l-green-500" : type === "error" ? "border-l-red-500" : type === "warning" ? "border-l-orange-500" : "border-l-blue-500"}
                            py-3 px-5
                            [grid-template-areas:_'title_action'_'description_action'] 
                            data-[swipe=cancel]:translate-x-0 
                            data-[swipe=move]:translate-x-[var(--radix-toast-swipe-move-x)] 
                            data-[state=closed]:animate-fadeOut 
                            data-[state=open]:animate-fadeIn 
                            `}
                        style={{ marginTop: 8 }}
                    >
                        <div className="flex justify-between items-center gap-2">
                            <div className="flex flex-col gap-1">
                                <ToastPrimitive.Title className=" text-base font-medium text-black [grid-area:_title]">{message}</ToastPrimitive.Title>
                                <ToastPrimitive.Description className="text-sm text-gray-500 [grid-area:_description]">
                                    {description}
                                </ToastPrimitive.Description>
                            </div>
                            <ToastPrimitive.Action
                                className="[grid-area:_action]"
                                asChild
                                altText="Goto schedule to undo"
                            >
                                <Button
                                    className="inline-flex h-[25px] items-center text-black border-none shadow-none justify-center bg-white rounded px-2 text-xs font-medium leading-[25px] hover:bg-gray-200 "
                                    onClick={() => handleClose(id)}
                                >
                                    <X />
                                </Button>
                            </ToastPrimitive.Action>
                        </div>
                    </ToastPrimitive.Root>
                ))}
            </ToastPrimitive.Provider>
        </ToastContext.Provider>
    );
}

export function useToast() {
    const ctx = React.useContext(ToastContext);
    if (!ctx) throw new Error("useToast必须在ToastProvider内使用");
    return ctx;
} 