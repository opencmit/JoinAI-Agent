'use client'

import "tdesign-react/es/_util/react-19-adapter";
import { useEffect, useState } from "react";

import { Button, DialogPlugin, MessagePlugin, NotificationPlugin, Popconfirm, Table, Form, Space, Select, Input, Dialog, Divider, Loading } from 'tdesign-react';
import type { FormProps, PageInfo, SortInfo, TableProps, TableRowData, TableSort } from 'tdesign-react';
import { MinusCircleIcon } from 'tdesign-icons-react';

import { apiClient } from "@/lib/api-client";

import { SearchItemsOptions, ListNamespaceOptions, StoreItem } from "@/types/langgraph";
import { formatDate } from "@/utils/date";
import { MarkdownText } from "../assistant-ui/markdown-text";

const { FormItem, FormList } = Form;

export function AdminStoreListComponent() {
    const [loading, setLoading] = useState<boolean>(false);
    const [storeList, setStoreList] = useState<StoreItem[]>([]);
    const [namespaceList, setNamespaceList] = useState<{ label: string, value: string }[]>([]);
    const [tableLoading, setTableLoading] = useState(true);
    const [namespaceListLoading, setNamespaceListLoading] = useState(true);
    const [total, setTotal] = useState(0);
    const [current, setCurrent] = useState(1);
    const [pageSize, setPageSize] = useState(10);
    const [namespaceCurrent, setNamespaceCurrent] = useState(1);
    const namespacePageSize = 10;

    const dialogType = "add";
    const [visibleDialog, setVisibleDialog] = useState(false);

    const [form] = Form.useForm();
    const namespace = Form.useWatch('namespace', form);
    const storeKey = Form.useWatch('storeKey', form);


    const [dialogForm] = Form.useForm();

    const [sort, setSort] = useState<SortInfo>({
        // 按照 status 字段进行排序
        sortBy: 'updated_at',
        // 是否按照降序进行排序
        descending: true,
    });

    const columns: TableProps['columns'] = [
        {
            align: 'center',
            colKey: 'key',
            title: 'key',
            minWidth: 100,
            ellipsis: true,
            sorter: true
        },
        {
            align: 'center',
            colKey: 'namespace',
            title: 'namespace',
            minWidth: 100,
            ellipsis: true,
            sorter: true
        },
        {
            align: 'center',
            colKey: 'value',
            title: 'value',
            width: 100,
            cell: ({ row }) => (
                <Button theme="primary" variant="text" onClick={() => handleViewConfig('value', row.value)}>
                    查看
                </Button>
            ),
        },
        {
            align: 'center',
            title: '创建时间',
            colKey: 'createdAt',
            minWidth: 180,
            sorter: true,
            cell: ({ row }) => (
                <span>{formatDate(row.createdAt, 'YYYY-MM-DD HH:mm:ss')}</span>
            ),
        },
        {
            align: 'center',
            title: '更新时间',
            colKey: 'updatedAt',
            minWidth: 180,
            sorter: true,
            cell: ({ row }) => (
                <span>{formatDate(row.updatedAt, 'YYYY-MM-DD HH:mm:ss')}</span>
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
                    <Button theme="warning" variant="text" onClick={() => handleUpdate(row)}>
                        修改
                    </Button>
                    <Popconfirm
                        theme={'danger'}
                        content={'确认删除该Thread吗'}
                        confirmBtn={
                            <Button size={'small'} theme="danger" onClick={() => handleDelete(row.namespace, row.key)}>
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

    const searchData = async (namespaceParam: string[], query: SearchItemsOptions) => {
        setTableLoading(true);
        try {
            // 构建查询参数
            const params: SearchItemsOptions = {};
            if (query.filter) params.filter = query.filter;
            if (query.limit) params.limit = query.limit;
            if (query.offset) params.offset = query.offset;
            if (query.query) params.query = query.query;
            if (query.refreshTtl) params.refreshTtl = query.refreshTtl;

            const response = await apiClient.searchLangGraphStoreList(namespaceParam, params);
            if (response.success) {
                setStoreList(response.data.items);
            } else {
                MessagePlugin.error(response.message);
            }
            console.log("searchLangGraphStoreList", response);
            setTotal(1000);
        } catch (error) {
            console.error("Error search store list:", error);
            MessagePlugin.error("获取存储列表失败");
        } finally {
            setTableLoading(false);
        }
    }

    const getData = async (namespaceParam: string[], keyParam: string) => {
        setTableLoading(true);
        try {
            const response = await apiClient.getLangGraphStoreList(namespaceParam, keyParam);
            if (response.success) {
                setStoreList(response.data);
            } else {
                MessagePlugin.error(response.message);
            }
            console.log("getOrUpdateLangGraphStoreList", response);
            setTotal(1);
        } catch (error) {
            console.error("Error get store list:", error);
            MessagePlugin.error("获取存储数据失败");
        } finally {
            setTableLoading(false);
        }
    }

    const fetchNamespaceData = async (query: ListNamespaceOptions) => {
        setNamespaceListLoading(true);
        try {
            // 构建查询参数
            const params: ListNamespaceOptions = {};
            if (query.prefix) params.prefix = query.prefix;
            if (query.suffix) params.suffix = query.suffix;
            if (query.maxDepth) params.maxDepth = query.maxDepth;
            if (query.limit) params.limit = query.limit;
            if (query.offset) params.offset = query.offset;

            const response = await apiClient.getLangGraphStoreNamespaceList(query);
            if (response.success) {
                const tempNamespaceList = [];
                for (const item of response.data.namespaces) {
                    for (const namespace of item) {
                        tempNamespaceList.push({
                            label: namespace,
                            value: namespace,
                        });
                    }
                }
                setNamespaceList(tempNamespaceList);
            } else {
                MessagePlugin.error(response.message);
            }
            setTotal(1000);
        } catch (error) {
            console.error("Error fetching namespace list:", error);
            MessagePlugin.error("获取namespace列表失败");
        } finally {
            setNamespaceListLoading(false);
        }
    }

    useEffect(() => {
        searchData([], {
            limit: pageSize,
            offset: (current - 1) * pageSize,
        });
        fetchNamespaceData({});
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

    const handleAdd = () => {
        console.log("handleAdd");
        setVisibleDialog(true);
    }

    const handleUpdate = (row: TableRowData) => {
        console.log("handleUpdate", row);

        const value = [];
        for (const key in row.value) {
            value.push({
                key: key,
                value: row.value[key],
            });
        }
        dialogForm.setFieldsValue({
            namespace: row.namespace,
            storeKey: row.key,
            value: value,
        });

        setVisibleDialog(true);
    }

    const handleAddConfirm = () => {
        console.log("handleAddConfirm", dialogForm.getFieldsValue(true));
        dialogForm.submit();
    }

    const onDialogSubmit: FormProps['onSubmit'] = async (e) => {
        setLoading(true);
        console.log(e);
        if (e.validateResult === true) {
            const values: Record<string, string> = {};
            const { namespace, storeKey, value } = dialogForm.getFieldsValue(true);
            console.log("onDialogSubmit", namespace, storeKey, value);
            for (const dict of value) {
                if (dict.key in values) {
                    NotificationPlugin.error({
                        title: '键名重复，请检查',
                        content: `重复键名：${dict.key}`,
                        placement: 'top-right',
                        duration: 3000,
                        offset: [-10, 10],
                        closeBtn: true,
                    });
                    setLoading(false);
                    return;
                } else {
                    values[dict.key] = dict.value;
                }
            }
            console.log("onDialogSubmit values", values);

            const response = await apiClient.putLangGraphStoreList(namespace, storeKey, values);
            if (response.success) {
                NotificationPlugin.success({
                    title: '新增store完成',
                    placement: 'top-right',
                    duration: 3000,
                    offset: [-10, 10],
                    closeBtn: true,
                });
                setVisibleDialog(false);
            } else {
                NotificationPlugin.error({
                    title: '新增store失败',
                    content: response.message,
                    placement: 'top-right',
                    duration: 3000,
                    offset: [-10, 10],
                    closeBtn: true,
                });
            }

            searchData(namespace, {
                limit: pageSize,
                offset: (current - 1) * pageSize,
            });
            setLoading(false);
        }
    };

    const handleOnCreate = (newValue: string | number) => {
        console.log("handleOnCreate", newValue);
        setNamespaceList((prev) => (prev.concat([{ label: newValue as string, value: newValue as string }])));
    };

    const handleDelete = async (namespace: string[], key: string) => {
        console.log("handleDelete", namespace, key);
        setTableLoading(true);
        await apiClient.deleteLangGraphStoreList(
            namespace,
            key
        );

        if (storeKey) {
            getData(namespace, storeKey);
        } else {
            searchData(namespace, {
                limit: pageSize,
                offset: (current - 1) * pageSize,
            });
        }

        NotificationPlugin.success({
            title: '删除store完成',
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
        searchData(namespace, {
            limit: pageSize,
            offset: (current - 1) * pageSize,
        });
    }
    const onSortChange = (sort: TableSort) => {
        console.log("onSortChange", sort);
        const sortInfo = sort as SortInfo;

        setSort(sortInfo);
        searchData(namespace, {
            limit: pageSize,
            offset: (current - 1) * pageSize,
        });
    };

    const onSubmit: FormProps['onSubmit'] = (e) => {
        console.log(e);
        if (e.validateResult === true) {
            if (storeKey) {
                getData(namespace, storeKey);
            } else {
                searchData(namespace, {
                    limit: pageSize,
                    offset: (current - 1) * pageSize,
                });
            }
        }
    };

    const onReset: FormProps['onReset'] = (e) => {
        console.log(e);
        MessagePlugin.info('重置成功');
        setCurrent(1);
        setPageSize(10);
        if (storeKey) {
            getData(namespace, storeKey);
        } else {
            searchData(namespace, {
                limit: pageSize,
                offset: 0,
            });
        }
    };

    // 通过滚动触底事件加载更多数据
    const handleScrollToBottom = () => {
        if (namespaceList.length < namespacePageSize * namespaceCurrent) {
            return;
        }

        fetchNamespaceData({
            prefix: [],
            suffix: [],
            maxDepth: 10,
            limit: namespacePageSize,
            offset: (namespaceCurrent + 1) * namespacePageSize,
        });
        setNamespaceCurrent((prev) => prev + 1);
    };


    return (
        <div className="h-screen w-full p-4 flex flex-col gap-4">
            <div className="h-fit w-full p-4 overflow-hidden rounded-lg bg-white">
                <Form
                    form={form}
                    onSubmit={onSubmit}
                    onReset={onReset}
                    colon
                    labelWidth={100}
                    resetType='initial'
                    initialData={{
                        namespace: [],
                        storeKey: ""
                    }}
                    layout='inline'
                >
                    <FormItem label="Namespace" name="namespace">
                        <Select
                            loading={namespaceListLoading}
                            options={namespaceList}
                            clearable
                            popupProps={{
                                onScrollToBottom: handleScrollToBottom,
                            }}
                            multiple
                        />
                    </FormItem>
                    <FormItem label="key" name="storeKey">
                        <Input />
                    </FormItem>
                    <FormItem style={{ marginLeft: 100, right: 0 }}>
                        <Space>
                            <Button type="submit" theme="primary" disabled={namespaceListLoading || tableLoading}>
                                提交
                            </Button>
                            <Button type="reset" theme="default" disabled={namespaceListLoading || tableLoading}>
                                重置
                            </Button>
                            <Button theme="primary" disabled={namespaceListLoading || tableLoading} onClick={handleAdd}>
                                新增
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
                    data={storeList}
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

            {/* 新增或更新对话框 */}
            <Dialog
                header={dialogType === "add" ? "新增" : "更新"}
                visible={visibleDialog}
                confirmBtn="提交"
                cancelBtn="取消"
                onClose={() => { setVisibleDialog(false); dialogForm.reset() }}
                onConfirm={handleAddConfirm}
                style={{
                    width: 'calc(var(--spacing) * 200)',
                } as React.CSSProperties}
            >
                <Form
                    className="p-4"
                    form={dialogForm}
                    onSubmit={onDialogSubmit}
                    colon
                    labelWidth={100}
                    resetType='initial'
                    style={{
                        maxHeight: 'calc(var(--spacing) * 140)',
                        overflowY: 'auto',
                    } as React.CSSProperties}
                >
                    <FormItem label="Namespace" name="namespace" initialData={[]} requiredMark>
                        <Select
                            loading={namespaceListLoading}
                            options={namespaceList}
                            clearable
                            popupProps={{
                                onScrollToBottom: handleScrollToBottom,
                            }}
                            filterable
                            creatable
                            multiple
                            onCreate={handleOnCreate}
                        />
                    </FormItem>
                    <FormItem label="key" name="storeKey" initialData="" requiredMark>
                        <Input />
                    </FormItem>
                    <Divider
                        align="left"
                        layout="horizontal"
                    >
                        Value内容
                    </Divider>
                    <FormList name="value">
                        {(fields, { add, remove }) => (
                            <>
                                {fields.map(({ key, name, ...restField }) => (
                                    <FormItem key={key}>
                                        <FormItem {...restField} name={[name, 'key']} label="key" rules={[{ required: true, type: 'error' }]}>
                                            <Input />
                                        </FormItem>
                                        <FormItem {...restField} name={[name, 'value']} label="value" rules={[{ required: true, type: 'error' }]}>
                                            <Input />
                                        </FormItem>

                                        <FormItem>
                                            <MinusCircleIcon size="20px" style={{ cursor: 'pointer' }} onClick={() => remove(name)} />
                                        </FormItem>
                                    </FormItem>
                                ))}
                                <FormItem style={{ marginLeft: 100 }}>
                                    <Button theme="default" variant="dashed" onClick={() => add({ key: '', value: '' })}>
                                        新增KV键值对
                                    </Button>
                                </FormItem>
                            </>
                        )}
                    </FormList>
                </Form>
            </Dialog>
            <Loading loading={loading} fullscreen preventScrollThrough={true} text="加载中"></Loading>
        </div>
    )
}