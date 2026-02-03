'use client'

import "tdesign-react/es/_util/react-19-adapter";
import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Button, DialogPlugin, MessagePlugin, NotificationPlugin, Popconfirm, Table, Tag, TagProps, Form, Space, Select } from 'tdesign-react';
import type { FormProps, PageInfo, SortInfo, TableProps, TableSort } from 'tdesign-react';
import { CopyIcon, ErrorCircleFilledIcon, CheckCircleFilledIcon, LoadIcon } from 'tdesign-icons-react';

import { apiClient } from "@/lib/api-client";

import { SearchAssistant, SearchThread, ThreadSortBy, Assistant } from "@/types/langgraph";
import { Thread, DefaultValues, } from "@langchain/langgraph-sdk";
import { formatDate } from "@/utils/date";
import { MarkdownText } from "../assistant-ui/markdown-text";

const { FormItem } = Form;

const statusNameListMap = {
    "idle": { label: '未开始', theme: 'default', icon: <CheckCircleFilledIcon /> },
    "busy": { label: '进行中', theme: 'primary', icon: <LoadIcon className="animate-spin" /> },
    "interrupted": { label: '任务中断', theme: 'warning', icon: <ErrorCircleFilledIcon /> },
    "error": { label: '任务异常', theme: 'danger', icon: <ErrorCircleFilledIcon /> },
};

const statusOptions = [
    { label: '未开始', value: 'idle' },
    { label: '进行中', value: 'busy' },
    { label: '任务中断', value: 'interrupted' },
    { label: '任务异常', value: 'error' },
]

interface AdminThreadListComponentProps {
    onSwitchToRun?: (threadId: string) => void;
    initialAssistantId?: string;
}

export function AdminThreadListComponent({ onSwitchToRun, initialAssistantId }: AdminThreadListComponentProps) {
    const [threadList, setThreadList] = useState<Thread<DefaultValues>[]>([]);
    const [assistantList, setAssistantList] = useState<Assistant[]>([]);
    const [tableLoading, setTableLoading] = useState(true);
    const [assistantListLoading, setAssistantListLoading] = useState(true);
    const [total, setTotal] = useState(0);
    const [current, setCurrent] = useState(1);
    const [pageSize, setPageSize] = useState(10);
    const [assistantCurrent, setAssistantCurrent] = useState(1);
    const assistantPageSize = 10;

    const [form] = Form.useForm();
    const assistantId = Form.useWatch('assistantId', form);
    const status = Form.useWatch('status', form);

    const [sort, setSort] = useState<SortInfo>({
        // 按照 status 字段进行排序
        sortBy: 'updated_at',
        // 是否按照降序进行排序
        descending: true,
    });

    const columns: TableProps['columns'] = [
        {
            align: 'center',
            colKey: 'title',
            title: '对话标题',
            minWidth: 200,
            ellipsis: true,
            fixed: 'left',
            cell: ({ row }) => (
                <span>{row.metadata.title}</span>
            ),
        },
        {
            align: 'center',
            colKey: 'status',
            title: '状态',
            width: 120,
            sorter: true,
            fixed: 'left',
            cell: ({ row }) => (
                <Tag
                    shape="round"
                    theme={statusNameListMap[row.status as keyof typeof statusNameListMap].theme as TagProps['theme']}
                    variant="light-outline"
                    icon={statusNameListMap[row.status as keyof typeof statusNameListMap].icon as TagProps['icon']}
                >
                    {statusNameListMap[row.status as keyof typeof statusNameListMap].label}
                </Tag>
            ),
        },
        {
            align: 'center',
            colKey: 'runCount',
            title: 'run',
            fixed: 'left',
            width: 190,
            cell: ({ row }) => (
                <div className="flex flex-row justify-center items-center gap-1">
                    <span>{row.runCount}个</span>

                    <Button
                        theme="primary"
                        variant="text"
                        onClick={() => onSwitchToRun?.(row.thread_id)}
                    >
                        查看
                    </Button>
                </div>
            ),
        },
        {
            align: 'center',
            colKey: 'thread_id',
            title: 'ID',
            width: 200,
            sorter: true,
            cell: ({ row }) => (
                <div className="flex flex-row justify-center items-center gap-2">
                    <span className="truncate">{row.thread_id}</span>
                    <motion.div
                        className="flex-1 cursor-pointer"
                        onClick={() => handleCopy(row.thread_id)}
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
            colKey: 'metadata',
            title: 'metadata',
            width: 100,
            cell: ({ row }) => (
                <Button theme="primary" variant="text" onClick={() => handleViewConfig('metadata', row.metadata)}>
                    查看
                </Button>
            ),
        },
        {
            align: 'center',
            colKey: 'values',
            title: 'values',
            width: 100,
            cell: ({ row }) => (
                <Button theme="primary" variant="text" onClick={() => handleViewConfig('values', row.values)}>
                    查看
                </Button>
            ),
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
                <span>{formatDate(row.created_at, 'YYYY-MM-DD HH:mm:ss')}</span>
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
                        content={'确认删除该Thread吗'}
                        confirmBtn={
                            <Button size={'small'} theme="danger" onClick={() => handleDelete(row.thread_id)}>
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

    const fetchData = async (query: SearchThread) => {
        setTableLoading(true);
        try {
            // 构建查询参数
            const params: SearchThread = {};
            if (query.metadata) params.metadata = query.metadata;
            if (query.limit) params.limit = query.limit;
            if (query.offset) params.offset = query.offset;
            if (query.status) params.status = query.status;
            if (query.sortBy) params.sortBy = query.sortBy;
            if (query.sortOrder) params.sortOrder = query.sortOrder;

            const response = await apiClient.getLangGraphThreadList(query);
            if (response.success) {
                for (const thread of response.data) {
                    try {
                        thread.runCount = await fetchRunData(thread.thread_id);
                    } catch {
                        thread.runCount = '--';
                    }
                }
                setThreadList(response.data);
            } else {
                MessagePlugin.error(response.message);
            }
            console.log("getLangGraphThreadList", response);
            setTotal(1000);
        } catch (error) {
            console.error("Error fetching thread list:", error);
            MessagePlugin.error("获取线程列表失败");
        } finally {
            setTableLoading(false);
        }
    }

    const fetchAssistantData = async (query: SearchAssistant) => {
        setAssistantListLoading(true);
        try {
            // 构建查询参数
            const params: SearchAssistant = {};
            if (query.graphId) params.graphId = query.graphId;
            if (query.limit) params.limit = query.limit;
            if (query.offset) params.offset = query.offset;
            if (query.sortBy) params.sortBy = query.sortBy;
            if (query.sortOrder) params.sortOrder = query.sortOrder;
            if (query.metadata) params.metadata = query.metadata;

            const response = await apiClient.getLangGraphAssistantList(query);
            if (response.success) {
                setAssistantList(response.data);
            } else {
                MessagePlugin.error(response.message);
            }
            setTotal(1000);
        } catch (error) {
            console.error("Error fetching assistant list:", error);
            MessagePlugin.error("获取助手列表失败");
        } finally {
            setAssistantListLoading(false);
        }
    }

    const fetchRunData = async (threadId: string) => {
        const response = await apiClient.getLangGraphRunList(threadId, {
            limit: 1000,
            offset: 0,
        });
        if (response.success) {
            return response.data.length;
        } else {
            throw new Error(`获取运行数量失败: ${response.message}`);
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

    useEffect(() => {
        if (initialAssistantId) {
            form.setFieldsValue({ assistantId: initialAssistantId });
            // 自动加载该 thread 的 runs
            fetchData({
                metadata: {
                    assistantId: initialAssistantId
                },
                limit: pageSize,
                offset: (current - 1) * pageSize,
                status: status ? status : undefined,
            });
        } else {
            fetchData({
                limit: pageSize,
                offset: (current - 1) * pageSize,
                sortBy: sort?.sortBy as ThreadSortBy,
                sortOrder: sort ? sort.descending ? "desc" : "asc" : undefined,
                status: status ? status : undefined,
            });
        }
        fetchAssistantData({
            limit: assistantPageSize,
            offset: 0,
            sortBy: "created_at",
            sortOrder: "desc",
        });
    }, []);

    const handleViewConfig = (title: string, content: object) => {
        console.log("handleViewConfig", content);
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

    const handleDelete = async (threadId: string) => {
        console.log("handleDelete", threadId);
        setTableLoading(true);
        await apiClient.deleteLangGraphThread(threadId);
        fetchData({
            limit: pageSize,
            offset: (current - 1) * pageSize,
            sortBy: sort?.sortBy as ThreadSortBy,
            sortOrder: sort ? sort.descending ? "desc" : "asc" : undefined,
            status: status ? status : undefined,
        });
        NotificationPlugin.success({
            title: '删除线程成功',
            placement: 'top-right',
            duration: 3000,
            offset: [-10, 10],
            closeBtn: true,
        });
        setTableLoading(false);
    }

    // 分页数据变化
    async function rehandleChange(pageInfo: PageInfo) {
        const { current, pageSize } = pageInfo;
        setCurrent(current);
        setPageSize(pageSize);
        await fetchData({
            metadata: {
                assistantId: assistantId ? assistantId : undefined,
            },
            limit: pageSize,
            offset: (current - 1) * pageSize,
            sortBy: sort?.sortBy as ThreadSortBy,
            sortOrder: sort ? sort.descending ? "desc" : "asc" : undefined,
            status: status ? status : undefined,
        });
    }
    const onSortChange = (sort: TableSort) => {
        console.log("onSortChange", sort);
        const sortInfo = sort as SortInfo;

        setSort(sortInfo);
        fetchData({
            metadata: {
                assistantId: assistantId ? assistantId : undefined,
            },
            limit: pageSize,
            offset: (current - 1) * pageSize,
            sortBy: sortInfo?.sortBy as ThreadSortBy,
            sortOrder: sortInfo ? sortInfo.descending ? "desc" : "asc" : undefined,
            status: status ? status : undefined,
        });
    };

    const onSubmit: FormProps['onSubmit'] = (e) => {
        console.log(e);
        if (e.validateResult === true) {
            fetchData({
                metadata: {
                    assistantId: assistantId ? assistantId : undefined,
                },
                limit: pageSize,
                offset: (current - 1) * pageSize,
                sortBy: sort?.sortBy as ThreadSortBy,
                sortOrder: sort ? sort.descending ? "desc" : "asc" : undefined,
                status: status ? status : undefined,
            });
        }
    };

    const onReset: FormProps['onReset'] = (e) => {
        console.log(e);
        MessagePlugin.info('重置成功');
        console.log("status", status);
        setCurrent(1);
        setPageSize(10);
        fetchData({
            metadata: {},
            limit: pageSize,
            offset: 0,
            sortBy: sort?.sortBy as ThreadSortBy,
            sortOrder: sort ? sort.descending ? "desc" : "asc" : undefined,
            status: undefined,
        });
    };

    // 通过滚动触底事件加载更多数据
    const handleScrollToBottom = () => {
        if (threadList.length < assistantPageSize * assistantCurrent) {
            return;
        }
        fetchAssistantData({
            limit: assistantPageSize,
            offset: (assistantCurrent + 1) * assistantPageSize,
            sortBy: "created_at",
            sortOrder: "desc",
        });
        setAssistantCurrent((prev) => prev + 1);
    };


    return (
        <div className="h-screen w-full p-4 flex flex-col gap-4">
            <div className="h-fit w-full p-4 overflow-hidden rounded-lg bg-white">
                <Form form={form} onSubmit={onSubmit} onReset={onReset} colon labelWidth={100} resetType='initial' layout='inline'>
                    <FormItem label="Assistant Id" name="assistantId" initialData="">
                        <Select
                            loading={assistantListLoading}
                            clearable
                            popupProps={{
                                // onScroll: handleScroll,
                                onScrollToBottom: handleScrollToBottom,
                            }}
                        >
                            {assistantList.map((item, index) => (
                                <Select.Option value={item.assistant_id} label={item.assistant_id} key={index}>
                                    {item.assistant_id}
                                </Select.Option>
                            ))}
                        </Select>
                    </FormItem>
                    <FormItem label="状态" name="status" initialData="">
                        <Select clearable>
                            {statusOptions.map((item, index) => (
                                <Select.Option value={item.value} label={item.label} key={index}>
                                    {item.label}
                                </Select.Option>
                            ))}
                        </Select>
                    </FormItem>
                    <FormItem style={{ marginLeft: 100, right: 0 }}>
                        <Space>
                            <Button type="submit" theme="primary" disabled={assistantListLoading || tableLoading}>
                                提交
                            </Button>
                            <Button type="reset" theme="default" disabled={assistantListLoading || tableLoading}>
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
                    data={threadList}
                    columns={columns}
                    disableDataPage={true}
                    stripe
                    sort={sort}
                    defaultSort={sort}
                    onSortChange={onSortChange}
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