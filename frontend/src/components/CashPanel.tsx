import { useEffect, useRef, useState } from "react";
import type { Cash } from "../types";

const money = (n: number) => n.toLocaleString("en-US", { style: "currency", currency: "USD" });
const reducedMotion = () => window.matchMedia("(prefers-reduced-motion: reduce)").matches;

/** Shows the balance, counting down to the new value and flashing a small "-$X". */
export function CashPanel({ cash }: { cash: Cash | null }) {
  const target = cash?.balance ?? null;
  const [shown, setShown] = useState<number | null>(target);
  const [delta, setDelta] = useState<number | null>(null);
  const previous = useRef<number | null>(target);

  useEffect(() => {
    if (target === null) return;
    const before = previous.current;
    previous.current = target;
    if (before === null || before === target) {
      setShown(target);
      return;
    }
    const change = target - before;
    setDelta(change);
    const timer = window.setTimeout(() => setDelta(null), 4000);
    if (reducedMotion()) {
      setShown(target);
      return () => window.clearTimeout(timer);
    }
    const start = performance.now();
    let frame = 0;
    const tick = (now: number) => {
      const t = Math.min((now - start) / 700, 1);
      setShown(before + change * t);
      if (t < 1) frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => {
      cancelAnimationFrame(frame);
      window.clearTimeout(timer);
    };
  }, [target]);

  return (
    <div className="cash" aria-label="Cash on hand">
      <span className="cash-label">{cash ? `${cash.account} balance` : "Checking balance"}</span>
      <span className="cash-amount" aria-live="polite">{shown === null ? "—" : money(shown)}</span>
      {delta !== null ? (
        <span className={`cash-delta ${delta < 0 ? "cash-delta--down" : "cash-delta--up"}`}>
          {delta < 0 ? "-" : "+"}{money(Math.abs(delta))}
        </span>
      ) : null}
      <span className="cash-date">Shop date: {cash?.shop_date ?? "—"}</span>
    </div>
  );
}
