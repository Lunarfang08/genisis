import Link from "next/link";

import { DemoWorld } from "@/app/_components/DemoWorld";

export default function DemoPage() {
  return (
    <main className="content-page">
      <Link className="detail-back" href="/">
        ← Project overview
      </Link>
      <span className="eyebrow">NO LOGIN / NO PAID SERVICES</span>
      <h1>Interactive demo world.</h1>
      <p>
        Change the seed, advance time, and verify that reset reproduces the same
        values.
      </p>
      <DemoWorld />
    </main>
  );
}
