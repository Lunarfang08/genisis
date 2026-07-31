import { redirect } from "next/navigation";

import { WorkspaceClient } from "@/app/_components/WorkspaceClient";
import { getCurrentUser, getWorlds } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function WorkspacePage({
  searchParams,
}: {
  searchParams: Promise<{ auth?: string }>;
}) {
  const user = await getCurrentUser();
  if (!user) redirect("/login");
  const worlds = await getWorlds();
  const authState = (await searchParams).auth;
  const initialNotice =
    authState === "registered"
      ? `Account created. Welcome, ${user.display_name}.`
      : authState === "signed-in"
        ? `Signed in. Welcome back, ${user.display_name}.`
        : "";
  return (
    <WorkspaceClient
      initialNotice={initialNotice}
      initialWorlds={worlds}
      user={user}
    />
  );
}
