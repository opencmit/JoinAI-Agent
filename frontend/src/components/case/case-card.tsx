'use client';

import "tdesign-react/es/_util/react-19-adapter";
import { useState } from "react";
import { redirect, RedirectType } from 'next/navigation'
import { AnimatePresence, motion } from "framer-motion";

import { Image } from 'tdesign-react';

import { Case } from "@/types/case";
import { buttonVariants } from "@/lib/animations";
import { Play } from "lucide-react";

export function CaseCardComponent({ caseItem }: { caseItem: Case }) {
    const [hover, setHover] = useState(false);

    return (
        <motion.div
            className="w-60 h-40 rounded-lg p-4 relative z-10 overflow-hidden"
            onMouseEnter={() => setHover(true)}
            onMouseLeave={() => setHover(false)}
            style={{ backgroundColor: caseItem.backgroundColor }}
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            transition={{ duration: 0.3, ease: "easeInOut" }}
        >
            <div className="h-full flex flex-row items-top justify-center">
                <span className="w-30 h-full text-wrap text-sm px-2 tracking-wide">{caseItem.title}</span>
                <Image
                    className="w-30 h-50"
                    src={caseItem.image}
                    fit="cover"
                    position="top"
                    shape="round"
                />
            </div>
            <AnimatePresence>
                {hover && (
                    <motion.div
                        className="w-full absolute bottom-0 left-0 right-0 z-20 bg-linear-to-t from-[#FFFFFF] via-[#FFFFFF] to-[#00000000] cursor-pointer items-center justify-center text-center flex flex-col gap-2 py-4"
                        initial={{ y: '100%', opacity: 0 }}
                        animate={{ y: 0, opacity: 1 }}
                        exit={{ y: '100%', opacity: 0 }}
                        transition={{ duration: 0.2, ease: 'easeInOut' }}
                    >
                        {/* <motion.div
                            className="w-30 bg-white rounded-full px-2 py-1 cursor-pointer border-1 border-gray-200 flex items-center justify-center gap-1 hover:bg-gray-100"
                            variants={buttonVariants}
                            initial="idle"
                            whileHover="hover"
                            whileTap="tap"
                        >
                            <MousePointerClick className="w-4 h-4" />
                            <span className="text-sm">做同款</span>
                        </motion.div> */}
                        <motion.div
                            className="w-30 bg-white rounded-full px-2 py-1 cursor-pointer border-1 border-gray-200 flex items-center justify-center gap-1 hover:bg-gray-100"
                            variants={buttonVariants}
                            initial="idle"
                            whileHover="hover"
                            whileTap="tap"
                            onClick={() => {
                                redirect(`/chat?caseId=${caseItem.id}`, RedirectType.replace);
                            }}
                        >
                            <Play className="w-4 h-4" />
                            <span className="text-sm">查看回放</span>
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>
        </motion.div>
    )
}