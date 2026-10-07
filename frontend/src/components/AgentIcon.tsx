import type { AgentId } from "../types";

/** Small, simple icons so each agent reads differently at a glance. */
export function AgentIcon({ id }: { id: AgentId }) {
  const common = { width: 28, height: 28, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: 1.8, strokeLinecap: "round", strokeLinejoin: "round", "aria-hidden": true } as const;
  switch (id) {
    case "boss": // a star in a badge
      return (<svg {...common}><circle cx="12" cy="12" r="9" /><path d="M12 7.2l1.5 3 3.3.5-2.4 2.3.6 3.3-3-1.6-3 1.6.6-3.3-2.4-2.3 3.3-.5z" /></svg>);
    case "inventory": // a box
      return (<svg {...common}><path d="M3.5 8L12 4l8.5 4v8L12 20l-8.5-4z" /><path d="M3.5 8L12 12l8.5-4M12 12v8" /></svg>);
    case "accounting": // a coin
      return (<svg {...common}><circle cx="12" cy="12" r="9" /><path d="M14.6 9.2c-.6-.8-1.5-1.1-2.6-1.1-1.4 0-2.4.7-2.4 1.8 0 2.6 5 1.2 5 3.8 0 1.2-1.1 2-2.6 2-1.2 0-2.200-.4-2.800-1.300M12 6.500v1.600M12 15.900v1.600" /></svg>);
    case "facilities": // a key
      return (<svg {...common}><circle cx="8" cy="12" r="3.5" /><path d="M11.5 12H21M18 12v3M15 12v2" /></svg>);
    default: // a speech bubble
      return (<svg {...common}><path d="M4 5h16v11H10l-4 4v-4H4z" /><path d="M8 9.500h8M8 12.500h5" /></svg>);
  }
}
