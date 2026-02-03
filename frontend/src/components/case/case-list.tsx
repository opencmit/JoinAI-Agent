'use client';

import "tdesign-react/es/_util/react-19-adapter";
import { AnimatePresence, motion } from "framer-motion";
import { useState } from "react";

import { CaseCardComponent } from "./case-card";
const Colors = [
    "rgb(238, 238, 246)",
    "rgb(246, 244, 240)",
    "rgb(238, 244, 248)",
    "rgb(246, 246, 246)"
]

const tabList = [
    {
        "name": "推荐案例",
        "id": "recommend"
    },
    {
        "name": "图片设计",
        "id": "design"
    },
    {
        "name": "网页设计",
        "id": "web-design"
    }
]

const cases = {
    "recommend": [
        {
            "id": "recommend-1",
            "title": "来帮我跑个文件看看效果吧",
            "image": "/case-1.png",
            "backgroundColor": Colors[Math.floor(Math.random() * Colors.length)]
        },
        {
            "id": "recommend-2",
            "title": "帮我查查北京未来5天啥天气",
            "image": "/case-2.jpg",
            "backgroundColor": Colors[Math.floor(Math.random() * Colors.length)]
        },
        {
            "id": "recommend-3",
            "title": "分分钟教孩子学会一元二次方程式",
            "image": "/case-3.jpg",
            "backgroundColor": Colors[Math.floor(Math.random() * Colors.length)]
        },
        {
            "id": "recommend-4",
            "title": "一分钟生成一张孩子嬉戏玩闹的图片",
            "image": "/case-3.jpg",
            "backgroundColor": Colors[Math.floor(Math.random() * Colors.length)]
        }
    ],
    "design": [
        {
            "id": "design-1",
            "title": "一分钟设计一张校庆海报",
            "image": "/case-4.jpg",
            "backgroundColor": Colors[Math.floor(Math.random() * Colors.length)]
        }
    ]
};

export function CaseListComponent() {
    const [selectedTab, setSelectedTab] = useState("recommend");

    return (
        <motion.div
            className="flex flex-col gap-4 w-4xl items-center"
            initial={{ opacity: 0, y: '100%' }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: '100%' }}
            transition={{ duration: 0.3, ease: "easeInOut" }}
        >

            <div className="w-full flex flex-row justify-start gap-4">
                {tabList.map((item, index) => {
                    return (
                        <div key={index} className="flex flex-row justify-center items-center" onClick={() => setSelectedTab(item.id)}>
                            <span className={`transition-all duration-300 ease-in-out ${selectedTab == item.id ? "text-[#010930]" : "text-gray-400 hover:text-gray-600"} cursor-pointer text-sm`}>{item.name}</span>
                        </div>
                    )
                })}
            </div>

            <AnimatePresence mode="wait">
                <div className="w-full flex flex-row flex-wrap justify-between gap-4">
                    {cases[selectedTab as keyof typeof cases].map((caseItem, index) => {
                        return (
                            <CaseCardComponent key={index} caseItem={caseItem} />
                        )
                    })
                    }
                </div>
            </AnimatePresence>
        </motion.div>
    )
}