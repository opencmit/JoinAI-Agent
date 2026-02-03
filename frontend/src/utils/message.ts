import { AIMessage } from "@noahlocal/copilotkit-shared";

export function showWebMessage(message: AIMessage, structureToolResults: Record<string, any>) {
    if (message.name === 'web') {
        if (structureToolResults[message.id] && Object.keys(structureToolResults[message.id]).length > 0) {
            return true;
        }
    }
    return false;
}