import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ApiError, api, friendlyError } from "./api";
import { AgentCards } from "./components/AgentCards";
import { AgentSummary } from "./components/AgentSummary";
import { ApprovalsPanel } from "./components/ApprovalsPanel";
import { CashPanel } from "./components/CashPanel";
import { Dan, type DanMood } from "./components/Dan";
import { Feed } from "./components/Feed";
import { TicketList } from "./components/TicketList";
import { deriveAgents, eventKey } from "./derive";
import { sound } from "./sound";
import type { AgentEvent, Approval, Cash, RunResult, Ticket } from "./types";

const POLL_MS = 1500;
const TREATS_KEY = "campus-customs-treats";

type Message = { tone: "ok" | "warn" | "error"; text: string } | null;

export default function App() {
  const [tickets, setTickets] = useState<Ticket[] | null>(null);
  const [cash, setCash] = useState<Cash | null>(null);
  const [approvals, setApprovals] = useState<Approval[]>([]);
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [backendDown, setBackendDown] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [runningId, setRunningId] = useState<number | null>(null);
  const [runResult, setRunResult] = useState<RunResult | null>(null);
  const [banner, setBanner] = useState<Message>(null);
  const [approvalMsg, setApprovalMsg] = useState<{ tone: "error" | "ok"; text: string } | null>(null);
  const [busyApproval, setBusyApproval] = useState<number | null>(null);
  const [resetting, setResetting] = useState(false);
  const [muted, setMuted] = useState(sound.isMuted());
  const [treats, setTreats] = useState(() => Number(localStorage.getItem(TREATS_KEY) ?? 0));
  const [treatTick, setTreatTick] = useState(0);
  const dialog = useRef<HTMLDialogElement>(null);

  // Refs that hold "what we have already seen" so each sound plays once, never on first load.
  const lastTimestamp = useRef<string | undefined>(undefined);
  const inFlight = useRef(false);
  const seen = useRef({ ready: false, tickets: new Map<number, string>(), approvals: new Map<number, string>(), agents: new Set<string>() });
  const runningRef = useRef<number | null>(null);
  runningRef.current = runningId;

  // Audio may only start after the user has clicked or pressed a key.
  useEffect(() => {
    const unlock = () => sound.unlock();
    window.addEventListener("pointerdown", unlock);
    window.addEventListener("keydown", unlock);
    return () => {
      window.removeEventListener("pointerdown", unlock);
      window.removeEventListener("keydown", unlock);
    };
  }, []);

  const refresh = useCallback(async (incremental: boolean) => {
    if (inFlight.current) return;
    inFlight.current = true;
    try {
      const [t, c, a, e] = await Promise.all([
        api.tickets(),
        api.cash(),
        api.approvals(),
        api.events(incremental ? lastTimestamp.current : undefined),
      ]);
      const s = seen.current;
      if (s.ready) {
        for (const ticket of t) if (s.tickets.get(ticket.id) === "open" && ticket.status === "resolved") sound.chime();
        for (const ap of a) {
          const before = s.approvals.get(ap.id);
          if (before === undefined && ap.status === "pending") sound.ding();
          if (before !== "executed" && ap.status === "executed") sound.coin();
        }
        if (runningRef.current !== null) {
          for (const ev of e) {
            const id = `${ev.run_id}:${ev.agent}`;
            if (!s.agents.has(id)) {
              s.agents.add(id);
              sound.blip();
            }
          }
        }
      }
      for (const ev of e) s.agents.add(`${ev.run_id}:${ev.agent}`);
      s.tickets = new Map(t.map((x) => [x.id, x.status]));
      s.approvals = new Map(a.map((x) => [x.id, x.status]));
      s.ready = true;

      setTickets(t);
      setCash(c);
      setApprovals(a);
      setEvents((old) => {
        const merged = incremental ? [...old] : [];
        const keys = new Set(merged.map(eventKey));
        for (const ev of e) if (!keys.has(eventKey(ev))) merged.push(ev);
        if (merged.length) lastTimestamp.current = merged[merged.length - 1].timestamp;
        else if (!incremental) lastTimestamp.current = undefined;
        return merged;
      });
      setBackendDown(false);
      setSelectedId((current) => current ?? t[0]?.id ?? null);
    } catch (error) {
      if (error instanceof ApiError && error.status === 0) setBackendDown(true);
    } finally {
      inFlight.current = false;
      setLoaded(true);
    }
  }, []);

  useEffect(() => {
    void refresh(false);
  }, [refresh]);

  // Poll every 1.5 s while a run is in progress; retry gently if the backend is unreachable.
  useEffect(() => {
    if (runningId === null) return;
    const timer = window.setInterval(() => void refresh(true), POLL_MS);
    return () => window.clearInterval(timer);
  }, [runningId, refresh]);
  useEffect(() => {
    if (!backendDown) return;
    const timer = window.setInterval(() => void refresh(false), 4000);
    return () => window.clearInterval(timer);
  }, [backendDown, refresh]);

  const selected = tickets?.find((t) => t.id === selectedId) ?? null;
  const running = runningId !== null;
  const ticketEvents = useMemo(() => events.filter((e) => e.ticket_id === selectedId), [events, selectedId]);
  const { views, runId } = useMemo(() => deriveAgents(events, selectedId, runningId === selectedId && running), [events, selectedId, runningId, running]);
  const hasRun = runId !== null;
  const report = runResult && runResult.ticket_id === selectedId ? runResult.report : null;

  const mood: DanMood = running ? "watching" : selected?.status === "resolved" ? "happy" : "sleepy";

  async function startRun() {
    if (selectedId === null || running) return;
    const id = selectedId;
    setBanner(null);
    setRunResult(null);
    setRunningId(id);
    try {
      const result = await api.run(id);
      setRunResult(result);
      if (result.ticket_status === "resolved") {
        setBanner({ tone: "ok", text: `Ticket #${id} is resolved.` });
      } else {
        const why = result.report?.summary ? ` The Boss said: ${result.report.summary}` : "";
        setBanner({ tone: "warn", text: `The agents finished, but ticket #${id} is not resolved yet.${why}` });
      }
    } catch (error) {
      setBanner({ tone: "error", text: friendlyError(error, "run") });
    } finally {
      setRunningId(null);
      await refresh(true); // one last refresh
    }
  }

  async function decide(id: number, action: "approve" | "reject", name: string) {
    setBusyApproval(id);
    setApprovalMsg(null);
    try {
      const result = action === "approve" ? await api.approve(id, name) : await api.reject(id, name);
      if (action === "approve" && result.payment) sound.coin();
      setApprovalMsg({
        tone: "ok",
        text: action === "approve" ? (result.payment ? "Approved and paid." : "Approved.") : "Rejected. No cash moved.",
      });
    } catch (error) {
      setApprovalMsg({ tone: "error", text: friendlyError(error, action) });
    } finally {
      setBusyApproval(null);
      await refresh(true);
    }
  }

  async function confirmReset() {
    dialog.current?.close();
    setResetting(true);
    try {
      await api.reset();
      lastTimestamp.current = undefined;
      seen.current = { ready: false, tickets: new Map(), approvals: new Map(), agents: new Set() };
      setEvents([]);
      setRunResult(null);
      setApprovalMsg(null);
      setBanner({ tone: "ok", text: "The desk was reset. Everything is back to the start." });
      await refresh(false);
    } catch (error) {
      setBanner({ tone: "error", text: friendlyError(error, "reset") });
    } finally {
      setResetting(false);
    }
  }

  function giveBone() {
    sound.happy();
    const next = treats + 1;
    setTreats(next);
    localStorage.setItem(TREATS_KEY, String(next));
    setTreatTick((n) => n + 1);
  }

  function toggleMute() {
    sound.unlock();
    sound.setMuted(!muted);
    setMuted(!muted);
  }

  return (
    <div className="app">
      <header className="top">
        <div className="mascot">
          <Dan mood={mood} treat={treatTick} />
        </div>
        <div className="title">
          <h1>Campus Customs Desk</h1>
          <p>
            {running ? "The team is on it. Dan is keeping an eye out." : selected?.status === "resolved" ? "Nicely done. Dan approves." : "Dan is dozing. Pick a ticket and wake the team."}
          </p>
        </div>
        <CashPanel cash={cash} />
        <div className="controls">
          <button type="button" className="btn btn--ghost" aria-pressed={muted} onClick={toggleMute}>
            {muted ? "🔇 Sounds off" : "🔊 Sounds on"}
          </button>
          <button type="button" className="btn btn--danger" disabled={running || resetting || backendDown} onClick={() => dialog.current?.showModal()}>
            {resetting ? "Resetting…" : "Reset desk"}
          </button>
        </div>
      </header>

      <div role="status" aria-live="polite" className="banner-region">
        {backendDown ? (
          <p className="banner banner--calm">
            Can't reach the backend yet. Start the backend first: <code>cd backend &amp;&amp; uvicorn main:app --reload --port 8000</code>. This page keeps checking.
          </p>
        ) : null}
        {banner ? <p className={`banner banner--${banner.tone}`}>{banner.text}</p> : null}
      </div>

      {!loaded ? <p className="empty loading">Loading the desk…</p> : null}

      {tickets ? (
        <main className="board">
          <section className="col col--tickets" aria-labelledby="tickets-title">
            <h2 id="tickets-title">Work orders</h2>
            {tickets.length === 0 ? <p className="empty">No tickets on the desk.</p> : null}
            <TicketList tickets={tickets} selectedId={selectedId} runningId={runningId} onSelect={(id) => !running && setSelectedId(id)} />
            <div className="run-box">
              <button
                type="button"
                className="btn btn--primary"
                disabled={running || !selected || selected.status === "resolved" || backendDown}
                onClick={startRun}
              >
                {running ? "Agents working…" : selected ? `Start the team on ticket #${selected.id}` : "Pick a ticket"}
              </button>
              {selected?.status === "resolved" ? <p className="hint">This ticket is already resolved.</p> : null}
              {running ? <p className="hint">This can take a few minutes. You can keep watching below.</p> : null}
            </div>
            <div className="bone-box">
              <button type="button" className="btn btn--bone" disabled={selected?.status !== "resolved"} onClick={giveBone}>
                🦴 Give Dan a bone
              </button>
              <span className="treats" aria-live="polite">Treats given: {treats}</span>
              {selected?.status !== "resolved" ? <p className="hint">Unlocks when the selected ticket is resolved.</p> : null}
            </div>
          </section>

          <div className="col col--agents">
            <AgentCards views={views} hasRun={hasRun} />
            <AgentSummary views={views} report={report} hasRun={hasRun} />
          </div>

          <div className="col col--side">
            <ApprovalsPanel approvals={approvals} busyId={busyApproval} message={approvalMsg} onDecide={decide} />
            <Feed events={ticketEvents} />
          </div>
        </main>
      ) : null}

      <dialog ref={dialog} className="dialog" aria-labelledby="reset-title">
        <h2 id="reset-title">Reset the desk?</h2>
        <p>This restores the database to how it started. Approvals, purchase orders, drafts and any payments will be wiped, and the board clears.</p>
        <div className="dialog-actions">
          <button type="button" className="btn btn--ghost" onClick={() => dialog.current?.close()}>Keep everything</button>
          <button type="button" className="btn btn--danger" onClick={confirmReset}>Yes, reset</button>
        </div>
      </dialog>
    </div>
  );
}
