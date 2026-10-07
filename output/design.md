# Dashboard design

The dashboard (`frontend/`, React + Vite + TypeScript) is a cozy shop desk where a human watches the agents work and makes every payment decision.

**Layout.** Three columns on a wide screen, one column on a narrow one. Left: the three tickets as paper work orders, the run button and the bone game. Middle: the five agent cards and a short "what each agent did" summary. Right: approvals and the activity feed. A navy header holds Dan, the checking balance with the shop date, the mute button and the reset button.

**Agents read differently.** Each agent has its own accent color, a small icon, a one-line personality (for example "Careful penny-watcher" for Accounting), a status pill (idle, working, delegating, done), a speech bubble with the latest thing it said, and chips for the MCP tools it used. Handoffs show up as "Boss handed this to Inventory" in the feed and as arrow chips on the card. Everything is derived from the audit events; the page keeps no agent state of its own.

**Resolved tickets and cash.** When the Boss reports the work complete, the work order gets a "RESOLVED" stamp that thumps down, Dan turns happy, and a chime plays. If a run ends without resolving, the page says so plainly with the Boss's summary. The balance counts down to its new value after an approved payment, with a small "-$X" shown for a few seconds and a low coin sound. Humans approve or reject in the Approvals panel; the buttons stay disabled until the person types their own name (the app never fills it in), and the backend's 403 and 409 answers are shown in friendly words.

**Mascot.** Dan the Bulldog is an original drawing made of simple inline SVG shapes. It is inspired by Yale's bulldog tradition as a friendly nod only; it uses no official artwork, logo, wordmark or crest. He dozes when idle, watches when agents work, and is happy when a ticket is resolved.

**Theme and font.** Navy, baby blue and a warm off-white paper tone, all CSS variables. The font is EB Garamond (stack: "EB Garamond", Garamond, "Cormorant Garamond", Georgia, serif), bundled through npm so nothing loads from the internet.

**Sounds.** Soft, short Web Audio tones (no audio files): a chime on resolve, a blip when an agent starts, a ding when an approval is requested, a low coin on payment, and a happy tune for the bone. Each plays once, quietly. Nothing plays before the first click, and the mute button remembers its setting.

**Bone game.** After the selected ticket is resolved, "Give Dan a bone" unlocks. Each click makes Dan hop happily and adds to a treats counter. There is no score or timer, and the dashboard works fine without it. I used a button rather than drag and drop to keep it simple and keyboard friendly.

**Accessibility.** Mute button; animations switch off under `prefers-reduced-motion`; navy text on paper for strong contrast; every control reachable and operable by keyboard with a visible focus ring; the reset confirmation uses a native dialog; status and error messages are announced through live regions; the feed can be collapsed; and the layout stays usable on a narrow window.
