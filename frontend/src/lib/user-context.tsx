"use client";

import React, { createContext, useContext, useState, ReactNode } from "react";

interface UserContextType {
    userId: string;
    userName: string;
    orgId: string;
    setUserId: (userId: string) => void;
    setUserName: (userName: string) => void;
    setOrgId: (orgId: string) => void;
}

const UserContext = createContext<UserContextType | undefined>(undefined);

export const UserProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
    const [userId, setUserId] = useState<string>("12345678-1234-1234-1234-123456789012");
    const [userName, setUserName] = useState<string>("test-name");
    const [orgId, setOrgId] = useState<string>("test-org");

    return (
        <UserContext.Provider value={{
            userId,
            userName,
            orgId,
            setUserId,
            setUserName,
            setOrgId,
        }}>
            {children}
        </UserContext.Provider>
    );
};

export function useUserContext() {
    const context = useContext(UserContext);
    if (!context) {
        throw new Error("useUserContext 必须在 UserProvider 内部使用");
    }
    return context;
} 