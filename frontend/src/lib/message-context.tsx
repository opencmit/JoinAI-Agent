"use client";

import React, { createContext, useContext, useCallback, ReactNode, useRef } from "react";

interface MessageContextType {
    setMessage: (inputMessage: string, inputMode: string, inputAgentType: string, inputFiles: string[]) => void;
    getAgentInfo: () => { mode: string, agentType: string, files: string[] };
    getMessage: () => string;
    isInit: () => boolean;
}

const MessageContext = createContext<MessageContextType | undefined>(undefined);

export const MessageProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
    const message = useRef<string>("");
    const mode = useRef<string>("");
    const agentType = useRef<string>("");
    const init = useRef<boolean>(false);
    const files = useRef<string[]>([]);

    const setMessage = useCallback((inputMessage: string, inputMode: string, inputAgentType: string, inputFiles: string[]) => {
        message.current = inputMessage;
        mode.current = inputMode;
        agentType.current = inputAgentType;
        files.current = inputFiles;
        init.current = true;
    }, []);

    const getAgentInfo = useCallback(() => {
        return {
            mode: mode.current,
            agentType: agentType.current,
            files: files.current
        };
    }, []);

    const getMessage = useCallback(() => {
        init.current = false;
        return message.current;
    }, []);

    const isInit = useCallback(() => {
        return init.current;
    }, []);

    return (
        <MessageContext.Provider value={{
            setMessage,
            getAgentInfo,
            getMessage,
            isInit,
        }}>
            {children}
        </MessageContext.Provider>
    );
};

export function useMessageContext() {
    const context = useContext(MessageContext);
    if (!context) {
        throw new Error("useMessageContext 必须在 MessageProvider 内部使用");
    }
    return context;
} 