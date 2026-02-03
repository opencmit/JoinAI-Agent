export interface AttachmentInfo {
    id: string; // 文件ID
    name: string; // 文件名称
    path: string; // 文件路径
    saveName: string; // 文件保存名称
    savePath: string; // 文件保存路径
    status: ATTACHMENT_STATUS; // 文件状态
    size: string; // 文件大小
    extension: string; // 文件扩展名
}

export type ATTACHMENT_STATUS = "pending" | "processing" | "completed" | "failed";