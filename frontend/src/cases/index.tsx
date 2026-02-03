import { web_search } from './web_search';
import { web_search_2 } from './web_search_2';
import { generate_html } from './generate_html';
import { poster } from './poster';
import { mcp_tool_1 } from './mcp_tool_1';

export type CASE_TYPE = "config" | "log-new" | "log-previous" | "message" | "message-user" | "message-file" | "message-terminal" | "message-design" | "message-tool";

export const CASE_MESSAGE = {
    "recommend-1": web_search,
    "recommend-2": web_search_2,
    "recommend-3": generate_html,
    "recommend-4": mcp_tool_1,
    "design-1": poster,
}