'use client'

import "tdesign-react/es/_util/react-19-adapter";
import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Button, DialogPlugin, MessagePlugin, NotificationPlugin, Popconfirm, Table, Form, Input, Space } from 'tdesign-react';
import type { PageInfo, TableProps, FormProps, TableSort, SortInfo } from 'tdesign-react';
import { CopyIcon } from 'tdesign-icons-react';

import { MarkdownText } from "@/components/assistant-ui/markdown-text";
import { apiClient } from "@/lib/api-client";

import { Assistant, AssistantSortBy, SearchAssistant } from "@/types/langgraph";
import { formatDate } from "@/utils/date";

const { FormItem } = Form;

interface AdminAssistantListComponentProps {
    onSwitchToThread?: (assistantId: string) => void;
}

export function AdminAssistantListComponent({ onSwitchToThread }: AdminAssistantListComponentProps) {
    const [assistantList, setAssistantList] = useState<Assistant[]>([]);
    const [tableLoading, setTableLoading] = useState(true);
    const [total, setTotal] = useState(0);
    const [current, setCurrent] = useState(1);
    const [pageSize, setPageSize] = useState(20);
    const [mounted, setMounted] = useState(false);

    const [form] = Form.useForm();
    const graphId = Form.useWatch('graphId', form);

    const [sort, setSort] = useState<SortInfo>({
        // 按照 status 字段进行排序
        sortBy: 'updated_at',
        // 是否按照降序进行排序
        descending: true,
    });

    const columns: TableProps['columns'] = [
        {
            align: 'center',
            colKey: 'name',
            title: '名称',
            width: 120,
            ellipsis: true,
            sorter: true,
            fixed: 'left'
        },
        {
            align: 'center',
            colKey: 'threadCount',
            title: 'thread',
            fixed: 'left',
            width: 190,
            cell: ({ row }) => (
                <div className="flex flex-row justify-center items-center gap-1">
                    <span>{row.threadCount}个</span>

                    <Button theme="primary" variant="text" onClick={() => onSwitchToThread?.(row.assistant_id)}>
                        查看
                    </Button>
                </div>
            ),
        },
        {
            align: 'center',
            colKey: 'assistant_id',
            title: 'ID',
            width: 150,
            sorter: true,
            cell: ({ row }) => (
                <div className="flex flex-row justify-center items-center gap-2">
                    <span className="truncate">{row.assistant_id}</span>
                    <motion.div
                        className="flex-1 cursor-pointer"
                        onClick={() => handleCopy(row.assistant_id)}
                        variants={{
                            idle: { scale: 1, color: "oklch(21% 0.034 264.665)" },
                            hover: { scale: 1.05, color: "oklch(70.7% 0.165 254.624)" },
                            tap: { scale: 0.95, color: "oklch(54.6% 0.245 262.881)", rotate: -20, translateY: -2, translateX: -2 }
                        }}
                        initial="idle"
                        whileHover="hover"
                        whileTap="tap"
                    >
                        <CopyIcon className="text-blue-500 hover:text-blue-700" />
                    </motion.div>
                </div>
            ),
        },
        {
            align: 'center',
            colKey: 'description',
            title: '描述',
            width: 100,
            ellipsis: true,
            sorter: true
        },
        {
            align: 'center',
            colKey: 'metadata',
            title: 'metadata',
            width: 100,
            cell: ({ row }) => (
                <div className="flex gap-2">
                    <Button theme="primary" variant="text" onClick={() => handleView('metadata', row.metadata)}>
                        查看
                    </Button>
                    {/* <Button theme="primary" variant="text" onClick={() => handleView('metadata', row.metadata)}>
                        修改
                    </Button> */}
                </div>
            ),
        },
        {
            align: 'center',
            colKey: 'config',
            title: 'config',
            width: 80,
            cell: ({ row }) => (
                <div className="flex gap-2">
                    <Button theme="primary" variant="text" onClick={() => handleView('config', row.config)}>
                        查看
                    </Button>
                    {/* <Button theme="primary" variant="text" onClick={() => handleView('config', row.config)}>
                        修改
                    </Button> */}
                </div>
            ),
        },
        {
            align: 'center',
            colKey: 'version',
            title: '版本',
            ellipsis: true,
        },
        {
            align: 'center',
            title: '创建时间',
            colKey: 'created_at',
            width: 180,
            sorter: true,
            cell: ({ row }) => (
                <span>{formatDate(row.created_at, 'YYYY-MM-DD HH:mm:ss')}</span>
            ),
        },
        {
            align: 'center',
            title: '更新时间',
            colKey: 'updated_at',
            width: 180,
            sorter: true,
            cell: ({ row }) => (
                <span>{formatDate(row.updated_at, 'YYYY-MM-DD HH:mm:ss')}</span>
            ),
        },
        {
            align: 'center',
            title: '操作',
            colKey: 'link',
            minWidth: 100,
            // 注意这种 JSX 写法需设置 <script lang="jsx" setup>
            cell: ({ row }) => (
                <div>
                    <Popconfirm
                        theme={'danger'}
                        content={'确认删除该Assistant吗'}
                        confirmBtn={
                            <Button size={'small'} theme="danger" onClick={() => handleDelete(row.assistant_id)}>
                                确定
                            </Button>
                        }>
                        <Button theme="danger" variant="text">
                            删除
                        </Button>
                    </Popconfirm>
                </div>
            ),
        },
    ];

    const fetchData = async (query: SearchAssistant) => {
        setTableLoading(true);
        try {
            // 构建查询参数
            const params: SearchAssistant = {};
            if (query.graphId) params.graphId = query.graphId;
            if (query.limit) params.limit = query.limit;
            if (query.offset) params.offset = query.offset;
            if (query.sortBy) params.sortBy = query.sortBy;
            if (query.sortOrder) params.sortOrder = query.sortOrder;
            if (query.metadata) params.metadata = query.metadata;

            const response = await apiClient.getLangGraphAssistantList(params);
            if (response.success) {
                for (const assistant of response.data) {
                    try {
                        assistant.threadCount = await fetchThreadCount(assistant.assistant_id);
                    } catch {
                        assistant.threadCount = '--';
                    }
                }
                setAssistantList(response.data);
            } else {
                MessagePlugin.error(response.message);
            }
            setTotal(1000);
        } catch (error) {
            console.error("Error fetching assistant list:", error);
            MessagePlugin.error("获取助手列表失败");
        } finally {
            setTableLoading(false);
        }
    }


    const fetchThreadCount = async (assistantId: string) => {
        const response = await apiClient.getLangGraphThreadList({
            metadata: {
                assistantId: assistantId
            },
            limit: 1000,
            offset: 0,
        });

        if (response.success) {
            return response.data.length;
        } else {
            throw new Error(`获取线程数量失败: ${response.message}`);
        }
    }

    const handleCopy = (text: string) => {
        try {
            navigator.clipboard.writeText(text);
            NotificationPlugin.success({
                title: '复制成功',
                content: text,
                placement: 'top-right',
                duration: 2000,
                offset: [-10, 10],
                closeBtn: true,
            });
        } catch (error) {
            console.error("Error copying text:", error);
            NotificationPlugin.error({
                title: '复制失败',
                content: text,
                placement: 'top-right',
                duration: 4000,
                offset: [-10, 10],
                closeBtn: true,
            });
        }
    }

    const handleView = (title: string, content: object) => {
        console.log("handleView", content);
        const confirmDialog = DialogPlugin.confirm({
            style: {
                width: 'calc(var(--spacing) * 200)',
            },
            header: title,
            body: <MarkdownText className="h-150 flex flex-col custom-scrollbar">{'```json\n' + JSON.stringify(content, null, 2) + '\n```'}</MarkdownText>,
            confirmBtn: '确认',
            cancelBtn: null,
            onConfirm: () => {
                confirmDialog.hide();
            },
            onClose: () => {
                confirmDialog.hide();
            },
        });
    }

    useEffect(() => {
        setMounted(true);
        fetchData({
            limit: pageSize,
            offset: (current - 1) * pageSize,
            sortBy: sort?.sortBy as AssistantSortBy,
            sortOrder: sort ? sort.descending ? "desc" : "asc" : undefined,
        });
    }, []);

    const handleDelete = async (assistantId: string) => {
        console.log("handleDelete", assistantId);
        setTableLoading(true);
        await apiClient.deleteLangGraphAssistant(assistantId);
        fetchData({
            limit: pageSize,
            offset: (current - 1) * pageSize,
            sortBy: sort?.sortBy as AssistantSortBy,
            sortOrder: sort ? sort.descending ? "desc" : "asc" : undefined,
        });
        NotificationPlugin.success({
            title: '删除助手成功',
            placement: 'top-right',
            duration: 3000,
            offset: [-10, 10],
            closeBtn: true,
        });
        setTableLoading(false);
    };

    // 分页数据变化
    async function rehandleChange(pageInfo: PageInfo) {
        const { current, pageSize } = pageInfo;
        setCurrent(current);
        setPageSize(pageSize);
        await fetchData({
            limit: pageSize,
            offset: (current - 1) * pageSize,
            sortBy: sort?.sortBy as AssistantSortBy,
            sortOrder: sort ? sort.descending ? "desc" : "asc" : undefined,
        });
    };

    const onSortChange = (sort: TableSort) => {
        console.log("onSortChange", sort);
        const sortInfo = sort as SortInfo;

        setSort(sortInfo);
        fetchData({
            graphId,
            limit: pageSize,
            offset: (current - 1) * pageSize,
            sortBy: sortInfo?.sortBy as AssistantSortBy,
            sortOrder: sortInfo ? sortInfo.descending ? "desc" : "asc" : undefined,
        });
    };

    const onSubmit: FormProps['onSubmit'] = (e) => {
        console.log(e);
        if (e.validateResult === true) {
            fetchData({
                graphId,
                limit: pageSize,
                offset: (current - 1) * pageSize,
                sortBy: sort?.sortBy as AssistantSortBy,
                sortOrder: sort ? sort.descending ? "desc" : "asc" : undefined,
            });
        }
    };

    const onReset: FormProps['onReset'] = (e) => {
        console.log(e);
        MessagePlugin.info('重置成功');
        setCurrent(1);
        setPageSize(10);
        fetchData({
            limit: pageSize,
            offset: 0,
            sortBy: sort?.sortBy as AssistantSortBy,
            sortOrder: sort ? sort.descending ? "desc" : "asc" : undefined,
        });
    };

    // 防止服务端渲染时的hydration mismatch
    if (!mounted) {
        return (
            <div className="h-screen w-full p-4">
                <div className="flex h-full w-full p-4 rounded-lg bg-white">
                    <div className="flex-1 flex items-center justify-center">
                        <div className="text-gray-500">加载中...</div>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="h-screen w-full p-4 flex flex-col gap-4">
            <div className="h-fit w-full p-4 overflow-hidden rounded-lg bg-white">
                <Form form={form} onSubmit={onSubmit} onReset={onReset} colon labelWidth={100} resetType='initial' layout='inline'>
                    <FormItem label="graphId" name="graphId" initialData="agent">
                        <Input />
                    </FormItem>
                    <FormItem style={{ marginLeft: 100, right: 0 }}>
                        <Space>
                            <Button type="submit" theme="primary" disabled={tableLoading}>
                                提交
                            </Button>
                            <Button type="reset" theme="default" disabled={tableLoading}>
                                重置
                            </Button>
                        </Space>
                    </FormItem>
                </Form>
            </div>
            <div className="flex-1 w-full p-4 overflow-hidden rounded-lg bg-white">
                <Table
                    className="h-full w-full"
                    rowKey="index"
                    loading={tableLoading}
                    data={assistantList}
                    columns={columns}
                    disableDataPage={true}
                    sort={sort}
                    defaultSort={sort}
                    onSortChange={onSortChange}
                    stripe
                    hover
                    pagination={{
                        current,
                        pageSize,
                        // 支持非受控用法
                        // defaultCurrent: 1,
                        // defaultPageSize: 5,
                        total,
                        showJumper: true,
                        onChange(pageInfo) {
                            console.log(pageInfo, 'onChange pageInfo');
                            rehandleChange(pageInfo);
                        },
                    }}
                    paginationAffixedBottom={{
                        container: 'div',
                    }}
                    headerAffixedTop={{
                        container: 'div',
                    }}
                />
            </div>
        </div>
    )
}