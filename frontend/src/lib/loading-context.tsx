"use client";

import React, { createContext, useContext, useState, ReactNode } from "react";

interface LoadingState {
    visible: boolean;
    text?: string;
}

interface LoadingContextType {
    loading: LoadingState;
    setLoading: (visible: boolean, text?: string) => void;
}

const LoadingContext = createContext<LoadingContextType | undefined>(undefined);

export const useLoading = () => {
    const context = useContext(LoadingContext);
    if (!context) {
        throw new Error("useLoading must be used within a LoadingProvider");
    }
    return context;
};

export const LoadingProvider = ({ children }: { children: ReactNode }) => {
    const [loading, setLoadingState] = useState<LoadingState>({ visible: false, text: undefined });
    const setLoading = (visible: boolean, text?: string) => {
        setLoadingState(prev => {
            if (visible) {
                return { visible, text };
            } else {
                return { ...prev, visible };
            }
        });
    };
    return (
        <LoadingContext.Provider value={{ loading, setLoading }}>
            {children}
        </LoadingContext.Provider>
    );
}; 