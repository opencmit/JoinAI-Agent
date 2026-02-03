"use client"

import * as React from "react";
import * as ToastPrimitive from "@radix-ui/react-toast";

export function Toast({ open, title, content, type }: { open: boolean, title: string, content: string, type: "success" | "error" | "warning" | "info" }) {

    // const handleClose = (id: number) => {
    //     setToasts((prev) => prev.filter((t) => t.id !== id));
    // };

    return (
        // <ToastContext.Provider {...props}>
        //     {children}
        //     <ToastPrimitive.Provider swipeDirection="up">
        // <ToastPrimitive.Viewport className="fixed top-0 left-1/2 z-[2147483647] m-0 flex w-[390px] max-w-[100vw] list-none flex-col gap-2.5 p-[var(--viewport-padding)] outline-none [--viewport-padding:_25px] -translate-x-1/2 items-center" />

        <ToastPrimitive.Root
            open={open}
            duration={2500}
            className={`
                            items-center 
                            rounded-md 
                            ${type === "success" ? "bg-green-200/50" : type === "error" ? "bg-red-200/50" : type === "warning" ? "bg-yellow-200/50" : "bg-blue-200/50"} 
                            ${type === "success" ? "text-green-500" : type === "error" ? "text-red-500" : type === "warning" ? "text-yellow-500" : "text-blue-500"} 
                            py-3 px-5
                            [grid-template-areas:_'title_action'_'description_action'] 
                            data-[swipe=cancel]:translate-x-0 
                            data-[swipe=move]:translate-x-[var(--radix-toast-swipe-move-x)] 
                            data-[state=closed]:animate-fadeOut 
                            data-[state=open]:animate-fadeIn 
                            `}
            style={{ marginTop: 8 }}
        >
            <ToastPrimitive.Title className=" text-[15px] font-medium text-slate12 [grid-area:_title]">{title}</ToastPrimitive.Title>
            {content && (
                <ToastPrimitive.Description>{content}</ToastPrimitive.Description>
            )}
        </ToastPrimitive.Root>
        //     </ToastPrimitive.Provider>
        // </ToastContext.Provider>
    );
}