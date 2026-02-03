import { redirect, RedirectType } from "next/navigation";

export default function Home() {
  console.log("这是page页面")

  redirect(`/chat`, RedirectType.replace);

  return (
    <div className="w-full h-screen overflow-hidden">
      <div className="h-full w-full overflow-hidden">
      </div>
    </div>
  );
}
