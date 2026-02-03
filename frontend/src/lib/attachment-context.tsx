"use client";

import React, { createContext, useContext, ReactNode, useRef, RefObject } from "react";

import { AttachmentInfo } from "@/types/attachment";
import { apiClient } from "./api-client";

interface AttachmentContextType {
    attachmentList: RefObject<AttachmentInfo[]>;
    setAttachmentList: (threadId: string, attachmentList: AttachmentInfo[] | ((prevAttachmentList: AttachmentInfo[]) => AttachmentInfo[])) => void;
}

const AttachmentContext = createContext<AttachmentContextType | undefined>(undefined);

export const AttachmentProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
    const attachmentList = useRef<AttachmentInfo[]>([]);

    const setAttachmentList = (threadId: string, tempAttachmentList: AttachmentInfo[] | ((prevAttachmentList: AttachmentInfo[]) => AttachmentInfo[])) => {
        const finalAttachmentList = typeof tempAttachmentList === 'function' ? tempAttachmentList(attachmentList.current) : tempAttachmentList;
        if (typeof tempAttachmentList === 'function') {
            attachmentList.current = finalAttachmentList;
        } else {
            attachmentList.current = finalAttachmentList;
        }

        // 更新langgraph中thread的metadata
        if (threadId) {
            apiClient.updateLangGraphThread(threadId, {
                metadata: {
                    attachmentList: finalAttachmentList
                }
            })
        }
    }

    return (
        <AttachmentContext.Provider value={{
            attachmentList,
            setAttachmentList
        }}>
            {children}
        </AttachmentContext.Provider>
    );
};

export function useAttachmentContext() {
    const context = useContext(AttachmentContext);
    if (!context) {
        throw new Error("useAttachmentContext 必须在 AttachmentProvider 内部使用");
    }
    return context;
} 