"use client";

import "tdesign-react/es/_util/react-19-adapter";
import { useState, useEffect, useRef } from "react";
import { motion } from "motion/react";
import { NotificationPlugin } from 'tdesign-react';
import { LoaderCircle, CircleX, Paperclip, CircleCheck } from "lucide-react";
import { v4 as uuidv4 } from 'uuid';

import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

import { useLoading } from "@/lib/loading-context";
import { useUserContext } from "@/lib/user-context";
import { apiClient } from "@/lib/api-client";
import { useAttachmentContext } from "@/lib/attachment-context";

import { AttachmentInfo } from "@/types/attachment";

interface FileUploaderProps {
    disabled?: boolean;
    threadId: string;
}

export const FileUploader: React.FC<FileUploaderProps> = ({ disabled, threadId }) => {
    // 附件相关状态
    const [uploading, setUploading] = useState<boolean>(false);
    const [popoverOpen, setPopoverOpen] = useState<boolean>(false);
    const { userId } = useUserContext();
    const { attachmentList, setAttachmentList, } = useAttachmentContext();

    const { setLoading } = useLoading();

    // 使用 ref 来存储最新的值，确保在异步操作中获取到最新值
    const userIdRef = useRef(userId);

    // 更新 ref 值
    useEffect(() => {
        userIdRef.current = userId;
    }, [userId]);

    const premitFileTypes = ["pdf", "docx", "xlsx", "txt", "md", "jpg", "png", "jpeg", "bmp"];

    // 文件上传处理，默认单次上传一个文件
    const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const files = e.target.files;
        if (!files || files.length === 0) {
            console.log('handleFileChange files异常，或files长度为0')
            NotificationPlugin.error({
                title: '文件异常',
                content: '请刷新页面后重试',
                placement: 'top-right',
                duration: 3000,
                offset: [-10, 10],
                closeBtn: true,
            });
            return;
        }

        const fileName = files[0].name;
        const fileType = files[0].name.toLowerCase().split('.').pop() ?? '';
        if (!premitFileTypes.includes(fileType)) {
            NotificationPlugin.error({
                title: '暂不支持上传该文件类型',
                content: '支持的文件类型为: ' + premitFileTypes.join(', '),
                placement: 'top-right',
                duration: 3000,
                offset: [-10, 10],
                closeBtn: true,
            });
            return;
        }

        setUploading(true);
        setLoading(true, "上传附件中");

        const attachment = {
            id: uuidv4(),
            name: fileName,
            path: "",
            saveName: "",
            savePath: "",
            status: "pending",
            size: files[0].size.toString(),
            extension: fileType,
        } as AttachmentInfo;

        const fileUploadResult = await handleFileUpload(files[0]);
        if (fileUploadResult.success) {
            attachment.saveName = fileUploadResult.saveName;
            attachment.savePath = fileUploadResult.savePath;
            attachment.status = "completed";

            NotificationPlugin.success({
                title: '上传成功',
                content: '已上传至附件列表：' + fileName,
                placement: 'top-right',
                duration: 3000,
                offset: [-10, 10],
            });

            setAttachmentList(threadId, (prevAttachmentList) => [...prevAttachmentList, attachment]);
        } else {
            NotificationPlugin.error({
                title: '文件上传失败',
                content: fileUploadResult.message,
                placement: 'top-right',
                duration: 3000,
                offset: [-10, 10],
                closeBtn: true,
            });
        }

        setLoading(false);
        setUploading(false);
        e.target.value = ""; // 重置input
    };

    // 处理文件 文件上传 操作
    const handleFileUpload = async (file: File): Promise<{ success: boolean, message: string, saveName: string, savePath: string }> => {
        // 创建FormData并添加文件和其他必要参数
        const traceId = uuidv4();
        const fileFormData = new FormData();
        fileFormData.append("file", file)
        fileFormData.append("traceId", traceId); // 生成唯一的traceId


        const fileUploadResult = await apiClient.fileUpload(fileFormData);
        console.log('文件上传接口返回：', fileUploadResult);

        if (fileUploadResult.success) {
            return {
                success: true,
                message: "",
                saveName: fileUploadResult.data.saveName,
                savePath: fileUploadResult.data.savePath,
            }
        } else {
            return {
                success: false,
                message: fileUploadResult.message,
                saveName: "",
                savePath: "",
            }
        }
    }

    // 删除单个文件
    const handleFileDelete = async (attachment: AttachmentInfo) => {
        if (!attachment) return;
        setLoading(true, "删除附件中");

        setAttachmentList(threadId, (prevAttachmentList) => prevAttachmentList.filter(f => f.id !== attachment.id));

        NotificationPlugin.success({
            title: '删除成功',
            content: '已从附件列表中删除：' + attachment.name,
            placement: 'top-right',
            duration: 3000,
            offset: [-10, 10],
        });

        setLoading(false);
    };

    return (
        <Popover open={popoverOpen} onOpenChange={setPopoverOpen}>
            <PopoverTrigger asChild>
                <Button
                    asChild
                    variant="outline"
                    className="h-9 rounded-sm border-none hover:bg-gray-100 text-sm shadow-none"
                    size="icon"
                    disabled={disabled}
                >
                    <motion.button
                        variants={{
                            idle: { scale: 1 },
                            hover: { scale: 1.05 },
                            tap: { scale: 0.95 },
                        }}
                        initial="idle"
                        whileHover="hover"
                        whileTap="tap"
                    >
                        <Paperclip className="w-6! h-6!" />
                    </motion.button>
                </Button>
            </PopoverTrigger>
            <PopoverContent align="start" side="bottom" className="p-4 w-100">
                <div className="flex flex-col gap-2">
                    <div className="block mb-1 flex justify-between">
                        <label className=" text-sm font-medium text-gray-700 ">上传文件</label>
                    </div>
                    <Input type="file" multiple disabled={uploading} onChange={handleFileChange} />
                    {uploading && <span className="text-xs text-gray-400">上传中...</span>}
                    <span className="text-xs text-gray-400">支持文件类型: doc, docx, xlsx, pdf, txt, md, jpg, png, jpeg, bmp</span>
                    <div className="mt-2">
                        <div className="flex flex-row items-center justify-between mb-1">
                            <span className="text-sm text-gray-500">已上传文件：</span>
                        </div>
                        <ul className="max-h-32 overflow-auto">
                            {attachmentList.current.length === 0 && <li className="text-xs text-gray-400">暂无文件</li>}
                            {attachmentList.current.map((attachment, index) => (
                                <li key={index} className="flex items-center justify-between text-xs py-1">
                                    <div className="flex items-center ">
                                        <span className="truncate max-w-40 mr-2 overflow-hidden text-ellipsis whitespace-nowrap" >
                                            {attachment.name}
                                        </span>

                                        {attachment.status == "completed" && <span className="flex items-center text-xs py-1 px-2 rounded-lg bg-green-100 text-green-500 max-w-30 text-xs"><CircleCheck className="w-4 h-4 mr-1" />上传完成</span>}
                                        {attachment.status == "processing" && <span className="flex items-center text-xs py-1 px-2 rounded-lg bg-blue-100 text-blue-500 max-w-30 text-xs"><LoaderCircle className="w-4 h-4 animate-spin mr-1" />处理中</span>}
                                        {attachment.status == "failed" && <span className="flex items-center text-xs py-1 px-2 rounded-lg bg-red-100 text-red-500 max-w-30 text-xs"><CircleX className="w-4 h-4 mr-1" />上传失败</span>}
                                    </div>
                                    <Button size="sm" variant="ghost" className="text-sm text-red-500 hover:bg-red-100 hover:text-red-500" onClick={() => handleFileDelete(attachment)}>删除</Button>
                                </li>
                            ))}
                        </ul>
                    </div>
                </div>
            </PopoverContent>
        </Popover>
    )
}