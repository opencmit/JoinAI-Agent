"use server"

import AdminPage from "./admin-page";

export default async function AdminRootPage() {

    return (
        <div className="w-full h-screen overflow-hidden">
            <AdminPage />
        </div>
    );
}
