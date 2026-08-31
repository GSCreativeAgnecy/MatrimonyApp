"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { tokenStore } from "@/lib/api";

export default function HomePage() {
  const router = useRouter();
  useEffect(() => {
    router.replace(tokenStore.get().access ? "/discover" : "/login");
  }, [router]);
  return null;
}