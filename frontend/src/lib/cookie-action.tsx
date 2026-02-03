'use server';

import { cookies } from 'next/headers'
import { redirect, RedirectType } from 'next/navigation'

export async function initCookies(userId: string, orgId: string, userName: string, threadId: string) {
    'use server';

    const cookieStore = await cookies()


    await cookieStore.set('userId', userId)
    await cookieStore.set('orgId', orgId)
    await cookieStore.set('userName', userName)

    if (threadId) {
        redirect(`/chat?threadId=${threadId}`, RedirectType.replace);
    } else {
        redirect(`/chat`, RedirectType.replace);
    }
}