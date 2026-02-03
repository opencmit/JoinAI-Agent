import * as React from "react";
import * as DialogPrimitive from "@radix-ui/react-dialog"
import { cn } from "@/lib/utils"

function DialogContent({
    className,
    children,
    ...props
}: React.ComponentProps<typeof DialogPrimitive.Content>) {
    return (
        <DialogPrimitive.Portal>
            <DialogPrimitive.Overlay className="z-100 fixed inset-0 bg-black/50 backdrop-blur-xs data-[state=open]:animate-contentIn data-[state=closed]:animate-contentOut " />
            <DialogPrimitive.Content
                data-slot="dialog-content"
                className={cn(
                    "z-200 fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 rounded-md bg-gray-800 p-[25px] shadow-[var(--shadow-6)] focus:outline-none data-[state=open]:animate-contentIn data-[state=closed]:animate-contentOut",
                    className
                )}
                {...props}
            >
                <DialogPrimitive.Title />
                <DialogPrimitive.Description />
                {children}
            </DialogPrimitive.Content>
        </DialogPrimitive.Portal>
    );
}

export const Dialog = DialogPrimitive.Root;
export const DialogTrigger = DialogPrimitive.Trigger;
export const DialogClose = DialogPrimitive.Close;

export {
    DialogContent
}