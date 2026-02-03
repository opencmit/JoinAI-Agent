"use client"

import { UserProvider } from "@/lib/user-context";
import "@noahlocal/copilotkit-react-ui/styles.css";
import "../globals.css";

export default function LoginRequiredLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <UserProvider>
            {children}
        </UserProvider>
    );
} 