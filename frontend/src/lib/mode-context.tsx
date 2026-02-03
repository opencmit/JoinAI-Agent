"use client";

import { createContext, useContext, useState, ReactNode } from "react";

interface ModeContextType {
    mode: string;
    setMode: (mode: string) => void;
}

const ModeContext = createContext<ModeContextType | undefined>(undefined);

export function ModeProvider({ children }: { children: ReactNode }) {
    const [mode, setMode] = useState("explore"); // 默认模式

    return (
        <ModeContext.Provider value={{ mode, setMode }}>
            {children}
        </ModeContext.Provider>
    );
}

export function useModeContext() {
    const context = useContext(ModeContext);
    if (!context) {
        throw new Error("useModeContext 必须在 ModeProvider 中使用");
    }
    return context;
}