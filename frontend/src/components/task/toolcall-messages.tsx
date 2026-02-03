"use client";
import { useCopilotChatInternal } from "@noahlocal/copilotkit-react-core";
import { ActionExecutionMessage, ResultMessage } from "@noahlocal/copilotkit-runtime-client-gql";

export interface ProcessedMessage {
    action: ActionExecutionMessage;
    results: ResultMessage[];
}

export function ToolCallMessages() {
    const {
        visibleMessages,
    } = useCopilotChatInternal();

    const processedMessages: ProcessedMessage[] = visibleMessages
        .filter((message): message is ActionExecutionMessage =>
            message.isActionExecutionMessage() && (message as ActionExecutionMessage).name !== 'message' && !(message as ActionExecutionMessage).name.startsWith("computer")
        )
        .map(actionMessage => {
            const resultMessages = visibleMessages.filter(
                resultMessage => resultMessage.isResultMessage() && resultMessage.actionExecutionId === actionMessage.id
            ) as ResultMessage[];
            return {
                action: actionMessage,
                results: resultMessages,
            };
        });

    return processedMessages
}