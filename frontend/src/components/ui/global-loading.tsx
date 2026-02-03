"use client";

import React from "react";
import { AnimatePresence } from "framer-motion";
import { useLoading } from "@/lib/loading-context";

export function GlobalLoading() {
    const { loading } = useLoading();
    return (
        <AnimatePresence>
            <div
                className={`${loading.visible ? "flex" : "hidden"} transition-opacity bg-black/50 backdrop-blur-xs duration-800 ease-in-out flex`}
                style={{
                    position: "fixed",
                    top: 0,
                    left: 0,
                    width: "100vw",
                    height: "100vh",
                    zIndex: 9999,
                    alignItems: "center",
                    justifyContent: "center",
                }}
            >
                <div style={{
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "center"
                }}>
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                    <div className="font-[PingFang_SC] text-white text-base after:content-[''] after:animate-dot-blink">{loading.text}</div>
                </div>
            </div>
        </AnimatePresence>
    );
};