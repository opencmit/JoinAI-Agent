'use client'

import "tdesign-react/es/_util/react-19-adapter";
import { useEffect, useState } from "react";

import { Button, DialogPlugin, MessagePlugin, NotificationPlugin, Popconfirm, Table, Tag, TagProps, Form, Space, Select } from 'tdesign-react';
import type { FormProps, PageInfo, TableProps } from 'tdesign-react';
import { ErrorCircleFilledIcon, CheckCircleFilledIcon, LoadIcon } from 'tdesign-icons-react';

import { apiClient } from "@/lib/api-client";

import { ListRuns, SearchThread } from "@/types/langgraph";
import { Thread, DefaultValues, Run } from "@langchain/langgraph-sdk";
import { formatDate } from "@/utils/date";
import { MarkdownText } from "../assistant-ui/markdown-text";

const { FormItem } = Form;

const statusNameListMap = {
    "pending": { label: '未开始', theme: 'default', icon: <CheckCircleFilledIcon /> },
    "running": { label: '进行中', theme: 'primary', icon: <LoadIcon className="animate-spin" /> },
    "interrupted": { label: '中断', theme: 'warning', icon: <ErrorCircleFilledIcon /> },
    "error": { label: '异常', theme: 'danger', icon: <ErrorCircleFilledIcon /> },
    "success": { label: '成功', theme: 'success', icon: <CheckCircleFilledIcon /> },
    "timeout": { label: '超时', theme: 'warning', icon: <ErrorCircleFilledIcon /> },
};

const statusOptions = [
    { label: '未开始', value: 'pending' },
    { label: '进行中', value: 'running' },
    { label: '异常', value: 'error' },
    { label: '成功', value: 'success' },
    { label: '超时', value: 'timeout' },
    { label: '中断', value: 'interrupted' },
]

interface AdminRunListComponentProps {
    initialThreadId?: string;
}

export function AdminRunListComponent({ initialThreadId }: AdminRunListComponentProps) {
    const [threadList, setThreadList] = useState<Thread<DefaultValues>[]>([]);
    const [runList, setRunList] = useState<Run[]>([]);
    const [tableLoading, setTableLoading] = useState(false);
    const [threadListLoading, setThreadListLoading] = useState(true);
    const [total, setTotal] = useState(0);
    const [current, setCurrent] = useState(1);
    const [pageSize, setPageSize] = useState(10);
    const [threadCurrent, setThreadCurrent] = useState(1);
    const threadPageSize = 10;

    const [form] = Form.useForm();
    const threadId = Form.useWatch('threadId', form);
    const status = Form.useWatch('status', form);

    const columns: TableProps['columns'] = [
        {
            align: 'center',
            colKey: 'run_id',
            title: 'ID',
            minWidth: 200,
            ellipsis: true,
        },
        {
            align: 'center',
            colKey: 'status',
            title: '状态',
            width: 120,
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
            colKey: 'title',
            title: '对话标题',
            minWidth: 200,
            ellipsis: true,
            cell: ({ row }) => (
                <span>{row.metadata.title}</span>
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
            colKey: 'kwargs',
            title: 'kwargs',
            width: 100,
            cell: ({ row }) => (
                <Button theme="primary" variant="text" onClick={() => handleViewConfig('kwargs', row.kwargs)}>
                    查看
                </Button>
            ),
        },
        {
            align: 'center',
            title: '创建时间',
            colKey: 'created_at',
            minWidth: 180,
            cell: ({ row }) => (
                <span>{formatDate(row.created_at, 'YYYY-MM-DD HH:mm:ss')}</span>
            ),
        },
        {
            align: 'center',
            title: '更新时间',
            colKey: 'updated_at',
            minWidth: 180,
            cell: ({ row }) => (
                <span>{formatDate(row.created_at, 'YYYY-MM-DD HH:mm:ss')}</span>
            ),
        },
        {
            align: 'center',
            title: '操作',
            colKey: 'link',
            minWidth: 500,
            // 注意这种 JSX 写法需设置 <script lang="jsx" setup>
            cell: ({ row }) => (
                <div>
                    <Popconfirm
                        theme={'danger'}
                        content={'确认停止该Run吗'}
                        confirmBtn={
                            <Button size={'small'} theme="danger" onClick={() => handleCancel(row.run_id)}>
                                确定
                            </Button>
                        }>
                        <Button theme="danger" variant="text">
                            停止
                        </Button>
                    </Popconfirm>
                    <Popconfirm
                        theme={'danger'}
                        content={'确认删除该Run吗'}
                        confirmBtn={
                            <Button size={'small'} theme="danger" onClick={() => handleDelete(row.run_id)}>
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

    const fetchData = async (threadId: string, query: ListRuns) => {
        setTableLoading(true);
        try {
            // 构建查询参数
            const params: ListRuns = {};
            if (query.limit) params.limit = query.limit;
            if (query.offset) params.offset = query.offset;
            if (query.status) params.status = query.status;

            const response = await apiClient.getLangGraphRunList(threadId, params);
            if (response.success) {
                setRunList(response.data);
            } else {
                MessagePlugin.error(response.message);
            }
            console.log("getLangGraphRunList", response);
            setTotal(1000);
        } catch (error) {
            console.error("Error fetching run list:", error);
            MessagePlugin.error("获取运行列表失败");
        } finally {
            setTableLoading(false);
        }
    }

    const fetchThreadData = async (query: SearchThread) => {
        setThreadListLoading(true);
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
                if (response.data[0] in threadList) {
                    return;
                }
                setThreadList((prev) =>
                    prev.concat(response.data),
                );
            } else {
                MessagePlugin.error(response.message);
            }
            console.log("getLangGraphThreadList", response);
            setTotal(1000);
        } catch (error) {
            console.error("Error fetching thread list:", error);
            MessagePlugin.error("获取线程列表失败");
        } finally {
            setThreadListLoading(false);
        }
    }

    useEffect(() => {
        fetchThreadData({
            limit: threadPageSize,
            offset: (threadCurrent - 1) * threadPageSize,
            sortBy: "created_at",
            sortOrder: "desc",
        });
    }, []);

    useEffect(() => {
        if (initialThreadId) {
            form.setFieldsValue({ threadId: initialThreadId });
            // 自动加载该 thread 的 runs
            fetchData(initialThreadId, {
                limit: pageSize,
                offset: (current - 1) * pageSize,
                status: status ? status : undefined,
            });
        }
    }, [initialThreadId]);

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

    const handleDelete = async (runId: string) => {
        console.log("handleDelete", runId);
        setTableLoading(true);
        await apiClient.deleteLangGraphRun(threadId, runId);
        fetchData("", {
            limit: pageSize,
            offset: (current - 1) * pageSize,
            status: status ? status : undefined,
        });
        NotificationPlugin.success({
            title: '删除运行完成',
            placement: 'top-right',
            duration: 3000,
            offset: [-10, 10],
            closeBtn: true,
        });
        setTableLoading(false);
    }

    const handleCancel = async (runId: string) => {
        console.log("handleCancel", threadId);
        setTableLoading(true);
        await apiClient.cancelLangGraphRun(threadId, runId);
        fetchData(threadId, {
            limit: pageSize,
            offset: (current - 1) * pageSize,
            status: status ? status : undefined,
        });
        NotificationPlugin.success({
            title: '取消运行完成',
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
        await fetchData("", {
            limit: pageSize,
            offset: (current - 1) * pageSize,
            status: status ? status : undefined,
        });
    }

    const onSubmit: FormProps['onSubmit'] = (e) => {
        console.log(e);
        if (e.validateResult === true) {
            fetchData(threadId, {
                limit: pageSize,
                offset: (current - 1) * pageSize,
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
        setThreadCurrent(1);
        fetchThreadData({
            limit: threadPageSize,
            offset: 0,
            sortBy: "created_at",
            sortOrder: "desc",
        });
    };

    // 通过滚动触底事件加载更多数据
    const handleScrollToBottom = () => {
        if (threadList.length < threadPageSize * threadCurrent) {
            return;
        }
        fetchThreadData({
            limit: threadPageSize,
            offset: (threadCurrent + 1) * threadPageSize,
            sortBy: "created_at",
            sortOrder: "desc",
        });
        setThreadCurrent((prev) => prev + 1);
    };

    return (
        <div className="h-screen w-full p-4 flex flex-col gap-4">
            <div className="h-fit w-full p-4 overflow-hidden rounded-lg bg-white">
                <Form form={form} onSubmit={onSubmit} onReset={onReset} colon labelWidth={100} resetType='initial' layout='inline'>
                    <FormItem label="Thread Id" name="threadId" initialData="">
                        <Select
                            loading={threadListLoading}
                            clearable
                            popupProps={{
                                // onScroll: handleScroll,
                                onScrollToBottom: handleScrollToBottom,
                            }}
                        >
                            {threadList.map((item, index) => (
                                <Select.Option value={item.thread_id} label={item.thread_id} key={index}>
                                    {item.thread_id}
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
                            <Button type="submit" theme="primary" disabled={threadListLoading || tableLoading}>
                                提交
                            </Button>
                            <Button type="reset" theme="default" disabled={threadListLoading || tableLoading}>
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
                    data={runList}
                    columns={columns}
                    disableDataPage={true}
                    stripe
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