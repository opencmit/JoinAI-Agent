
import { AGENT_TYPE } from "./agent"
import { AttachmentInfo } from "./attachment";

// 默认线程类型定义
export interface Thread {
    id: string;
    title: string;
    top: boolean;
    attachmentList: AttachmentInfo[];
    agentType: AGENT_TYPE,
    createdAt: Date;
    updatedAt: Date;
    status: string;
    values: any | null;
}

export const defaultThread: Thread = {
    id: "",
    title: "",
    top: false,
    attachmentList: [],
    agentType: "normal",
    createdAt: new Date(),
    updatedAt: new Date(),
    status: "",
    values: null
}