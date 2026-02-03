"use client"

import * as AlertDialogPrimitive from "@radix-ui/react-alert-dialog"

import { cn } from "@/lib/utils"

function AlertDialog({
    ...props
}: React.ComponentProps<typeof AlertDialogPrimitive.Root>) {
    return <AlertDialogPrimitive.Root data-slot="alert-dialog" {...props} />
}

function AlertDialogTrigger({
    ...props
}: React.ComponentProps<typeof AlertDialogPrimitive.Trigger>) {
    return <AlertDialogPrimitive.Trigger data-slot="alert-dialog-trigger" {...props} />
}

function AlertDialogPortal({
    ...props
}: React.ComponentProps<typeof AlertDialogPrimitive.Portal>) {
    return <AlertDialogPrimitive.Portal data-slot="alert-dialog-portal" {...props} />
}

function AlertDialogOverlay({
    className,
    ...props
}: React.ComponentProps<typeof AlertDialogPrimitive.Overlay>) {
    return <AlertDialogPrimitive.Overlay
        data-slot="alert-dialog-overlay"
        className={cn("z-300 bg-black/50 backdrop-blur-xs fixed inset-0 data-[state=open]:animate-overlayShow", className)}
        {...props}
    />
}

function AlertDialogDescription({
    ...props
}: React.ComponentProps<typeof AlertDialogPrimitive.Description>) {
    return <AlertDialogPrimitive.Description data-slot="alert-dialog-description" {...props} />
}

function AlertDialogTitle({
    ...props
}: React.ComponentProps<typeof AlertDialogPrimitive.Title>) {
    return <AlertDialogPrimitive.Title data-slot="alert-dialog-title" {...props} />
}

function AlertDialogContent({
    className,
    ...props
}: React.ComponentProps<typeof AlertDialogPrimitive.Content>) {
    return <AlertDialogPrimitive.Content
        data-slot="alert-dialog-content"
        className={cn("z-400 fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 rounded-md bg-white p-[25px] shadow-[var(--shadow-6)] focus:outline-none", className)}
        {...props}
    />
}

function AlertDialogCancel({
    ...props
}: React.ComponentProps<typeof AlertDialogPrimitive.Cancel>) {
    return <AlertDialogPrimitive.Cancel data-slot="alert-dialog-cancel" {...props} />
}

function AlertDialogAction({
    ...props
}: React.ComponentProps<typeof AlertDialogPrimitive.Action>) {
    return <AlertDialogPrimitive.Action data-slot="alert-dialog-action" {...props} />
}

export { AlertDialog, AlertDialogTrigger, AlertDialogContent, AlertDialogCancel, AlertDialogAction, AlertDialogPortal, AlertDialogOverlay, AlertDialogDescription, AlertDialogTitle }