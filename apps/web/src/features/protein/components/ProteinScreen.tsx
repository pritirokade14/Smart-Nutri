"use client";

import { ProteinSwaps } from "./ProteinSwaps";
import { ProteinView } from "./ProteinView";

/** The Protein screen: today's progress, then the higher-protein swaps. */
export function ProteinScreen() {
  return (
    <ProteinView>
      {(memberId) => <ProteinSwaps key={memberId} memberId={memberId} />}
    </ProteinView>
  );
}
