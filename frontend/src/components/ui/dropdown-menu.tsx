import * as React from "react";
import * as DropdownMenuPrimitive from "@radix-ui/react-dropdown-menu"
import { cn } from "@/lib/utils"
import {
    Check,
} from "lucide-react";

export const DropdownMenu = DropdownMenuPrimitive.Root;

function DropdownMenuTrigger({
    ...props
}: React.ComponentProps<typeof DropdownMenuPrimitive.Trigger>) {
    return <DropdownMenuPrimitive.Trigger data-slot="dropdown-menu-trigger" {...props} />
}
function DropdownMenuPortal({
    ...props
}: React.ComponentProps<typeof DropdownMenuPrimitive.Portal>) {
    return <DropdownMenuPrimitive.Portal data-slot="dropdown-menu-portal" {...props} />
}
function DropdownMenuContent({
    className,
    children,
    ...props
}: React.ComponentProps<typeof DropdownMenuPrimitive.Content>) {
    return (
        <DropdownMenuPrimitive.Portal>
            <DropdownMenuPrimitive.Content
                data-slot="dropdown-menu-content"
                className={cn(
                    "transition-all transition-discrete data-[side=bottom]:animate-slideUpAndFade data-[side=left]:animate-slideRightAndFade data-[side=right]:animate-slideLeftAndFade data-[side=top]:animate-slideDownAndFade",
                    className
                )}
                {...props}
            >
                {children}
                <DropdownMenuPrimitive.Arrow />
            </DropdownMenuPrimitive.Content>
        </DropdownMenuPrimitive.Portal>
    );
}

export const DropdownMenuLabel = DropdownMenuPrimitive.Label;
export const DropdownMenuItem = DropdownMenuPrimitive.Item;
export const DropdownMenuGroup = DropdownMenuPrimitive.Group;

function DropdownMenuCheckboxItem({
    ...props
}: React.ComponentProps<typeof DropdownMenuPrimitive.CheckboxItem>) {
    return <DropdownMenuPrimitive.CheckboxItem data-slot="dropdown-menu-checkboxitem" {...props} />
}

function DropdownMenuRadioGroup({
    ...props
}: React.ComponentProps<typeof DropdownMenuPrimitive.RadioGroup>) {
    return <DropdownMenuPrimitive.RadioGroup data-slot="dropdown-menu-radiogroup" {...props} />
}

function DropdownMenuRadioItem({
    className,
    children,
    ...props
}: React.ComponentProps<typeof DropdownMenuPrimitive.RadioItem>) {
    return (
        <DropdownMenuPrimitive.RadioItem
            data-slot="dropdown-menu-radioitem"
            className={cn(
                "data-[disabled]:bg-gray-100 data-[disabled]:text-gray-500",
                className
            )}
            {...props}
        >
            {children}
            <DropdownMenuPrimitive.ItemIndicator>
                <Check />
            </DropdownMenuPrimitive.ItemIndicator>
        </DropdownMenuPrimitive.RadioItem >
    );
    return <DropdownMenuPrimitive.RadioItem data-slot="dropdown-menu-radioitem" {...props} />
}

function DropdownMenuItemIndicator({
    ...props
}: React.ComponentProps<typeof DropdownMenuPrimitive.ItemIndicator>) {
    return <DropdownMenuPrimitive.ItemIndicator data-slot="dropdown-menu-itemindicator" {...props} />
}

function DropdownMenuSub({
    ...props
}: React.ComponentProps<typeof DropdownMenuPrimitive.Sub>) {
    return <DropdownMenuPrimitive.Sub data-slot="dropdown-menu-sub" {...props} />
}

function DropdownMenuSubTrigger({
    ...props
}: React.ComponentProps<typeof DropdownMenuPrimitive.SubTrigger>) {
    return <DropdownMenuPrimitive.SubTrigger data-slot="dropdown-menu-subtrigger" {...props} />
}

function DropdownMenuSubContent({
    ...props
}: React.ComponentProps<typeof DropdownMenuPrimitive.SubContent>) {
    return <DropdownMenuPrimitive.SubContent data-slot="dropdown-menu-subcontent" {...props} />
}

function DropdownMenuSeparator({
    ...props
}: React.ComponentProps<typeof DropdownMenuPrimitive.Separator>) {
    return <DropdownMenuPrimitive.Separator data-slot="dropdown-menu-separator" {...props} />
}

function DropdownMenuArrow({
    ...props
}: React.ComponentProps<typeof DropdownMenuPrimitive.Arrow>) {
    return <DropdownMenuPrimitive.Arrow data-slot="dropdown-menu-arrow" {...props} />
}

export {
    DropdownMenuTrigger,
    DropdownMenuPortal,
    DropdownMenuContent,
    DropdownMenuCheckboxItem,
    DropdownMenuRadioGroup,
    DropdownMenuRadioItem,
    DropdownMenuItemIndicator,
    DropdownMenuSub,
    DropdownMenuSubTrigger,
    DropdownMenuSubContent,
    DropdownMenuSeparator,
    DropdownMenuArrow
}
