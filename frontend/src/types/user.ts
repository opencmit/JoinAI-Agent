export interface OrgAndTeamInfo {
    orgId: string;
    orgName: string;
    teams: TeamInfo[];
    channels: ChannelInfo[];
}

export interface TeamInfo {
    teamId: string;
    teamName: string;
}

export interface ChannelInfo {
    channelId: string;
    channelName: string;
}