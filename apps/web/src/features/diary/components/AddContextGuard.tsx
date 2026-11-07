"use client";

import { usePathname } from "next/navigation";
import { useEffect } from "react";
import { clearDiaryAddContext, isAddTripPath } from "../lib/addContext";

/** Leaving the add-food trip (diary, search, scan, product) drops its context. */
export function AddContextGuard() {
  const pathname = usePathname();
  useEffect(() => {
    if (!isAddTripPath(pathname)) clearDiaryAddContext();
  }, [pathname]);
  return null;
}
