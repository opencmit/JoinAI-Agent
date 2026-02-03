export type BrowserUseSteps = {
    task_id?: string;
    session_id?: string;
    live_url?: string;
    total_steps: number;
    steps: BrowserUseStepItem[];
    is_success: boolean;
    task_output?: string;
};

export type BrowserUseStepItem = {
    step_number: number;
    goal?: string;
    evaluation?: string;
    memory: string;
    actions: (BrowserUseStepInputAction | BrowserUseStepClickAction | BrowserUseStepSwitchAction | BrowserUseStepScrollAction | BrowserUseStepDoneAction)[];
    url: string;
    screenshot_url: string;
    created_at: string;
}

export type BrowserUseStepInputAction = {
    input: {
        index: number;
        text: string;
        clear: boolean;
    };
};

export type BrowserUseStepClickAction = {
    click: {
        index: number;
    };
};

export type BrowserUseStepSwitchAction = {
    switch: {
        tab_id: string;
    };
};

export type BrowserUseStepScrollAction = {
    scroll: {
        down: boolean;
        pages: number;
    }
};

export type BrowserUseStepDoneAction = {
    done: {
        text: string;
        success: boolean;
        files_to_display: string[];
    };
};