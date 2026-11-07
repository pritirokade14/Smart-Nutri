"use client";

import { useEffect } from "react";
import { getMe, syncTimezone } from "@/lib/timezone";

/** Sends the browser's time zone once per session (renders nothing). */
export function TimezoneSync() {
  useEffect(() => {
    void getMe()
      .then(syncTimezone)
      .catch(() => {
        // Ignored: the account keeps its zone.
      });
  }, []);
  return null;
}
