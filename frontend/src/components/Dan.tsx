export type DanMood = "sleepy" | "watching" | "happy";

interface Props {
  mood: DanMood;
  treat: number; // changes each time a bone is given, to replay the happy hop
}

/**
 * Dan the Bulldog: an original drawing (simple shapes, no official artwork),
 * a friendly nod to the bulldog tradition. Sleepy when idle, perky while the
 * agents work, happy when a ticket is resolved.
 */
export function Dan({ mood, treat }: Props) {
  return (
    <svg
      key={treat}
      className={`dan dan--${mood} ${treat ? "dan--treat" : ""}`}
      viewBox="0 0 220 190"
      role="img"
      aria-label={
        mood === "sleepy" ? "Dan the Bulldog, dozing at the desk" : mood === "watching" ? "Dan the Bulldog, watching the agents work" : "Dan the Bulldog, happy"
      }
    >
      {/* the desk */}
      <rect x="0" y="150" width="220" height="40" rx="6" fill="var(--wood)" />
      <rect x="0" y="146" width="220" height="10" rx="5" fill="var(--wood-light)" />
      <rect x="150" y="132" width="52" height="16" rx="2" fill="var(--paper)" stroke="var(--line)" />
      <rect x="156" y="124" width="46" height="12" rx="2" fill="var(--paper)" stroke="var(--line)" />

      <g className="dan-body">
        {/* shoulders and collar */}
        <path d="M52 152 Q56 126 110 124 Q164 126 168 152 Z" fill="var(--fawn)" />
        <path d="M70 134 Q110 148 150 134 L150 144 Q110 158 70 144 Z" fill="var(--navy)" />
        <circle cx="110" cy="148" r="5" fill="var(--gold)" />

        <g className="dan-head">
          {/* ears */}
          <path className="ear ear-left" d="M62 72 Q44 52 58 40 Q78 44 84 66 Z" fill="var(--fawn-dark)" />
          <path className="ear ear-right" d="M158 72 Q176 52 162 40 Q142 44 136 66 Z" fill="var(--fawn-dark)" />
          {/* head, jowls and muzzle */}
          <ellipse cx="110" cy="92" rx="58" ry="46" fill="var(--fawn)" />
          <ellipse cx="78" cy="116" rx="22" ry="16" fill="var(--fawn)" />
          <ellipse cx="142" cy="116" rx="22" ry="16" fill="var(--fawn)" />
          <ellipse cx="110" cy="112" rx="32" ry="22" fill="var(--muzzle)" />
          {/* brow wrinkles */}
          <path d="M92 66 Q110 58 128 66" stroke="var(--fawn-dark)" strokeWidth="3" fill="none" strokeLinecap="round" />
          <path d="M98 73 Q110 68 122 73" stroke="var(--fawn-dark)" strokeWidth="2" fill="none" strokeLinecap="round" />
          {/* eyes */}
          <g className="eyes eyes-open">
            <circle cx="86" cy="88" r="7" fill="var(--ink)" />
            <circle cx="134" cy="88" r="7" fill="var(--ink)" />
            <circle cx="88" cy="85" r="2.3" fill="#fff" />
            <circle cx="136" cy="85" r="2.3" fill="#fff" />
          </g>
          <g className="eyes eyes-closed" stroke="var(--ink)" strokeWidth="3.5" strokeLinecap="round" fill="none">
            <path d="M78 90 Q86 96 94 90" />
            <path d="M126 90 Q134 96 142 90" />
          </g>
          <g className="eyes eyes-happy" stroke="var(--ink)" strokeWidth="3.5" strokeLinecap="round" fill="none">
            <path d="M78 92 Q86 82 94 92" />
            <path d="M126 92 Q134 82 142 92" />
          </g>
          {/* nose and mouth */}
          <ellipse cx="110" cy="102" rx="11" ry="7.5" fill="var(--ink)" />
          <ellipse cx="107" cy="99.5" rx="3" ry="1.6" fill="#fff" opacity="0.5" />
          <path d="M110 109 L110 114" stroke="var(--ink)" strokeWidth="2.5" strokeLinecap="round" />
          <path className="mouth mouth-calm" d="M94 116 Q102 122 110 114 Q118 122 126 116" stroke="var(--ink)" strokeWidth="2.5" fill="none" strokeLinecap="round" />
          <path className="mouth mouth-happy" d="M92 114 Q110 134 128 114" stroke="var(--ink)" strokeWidth="2.5" fill="var(--tongue)" strokeLinecap="round" strokeLinejoin="round" />
          <path d="M98 117 L101 123 L104 117 Z" fill="#fff" />
          <path d="M116 117 L119 123 L122 117 Z" fill="#fff" />
        </g>
      </g>

      {/* mood extras */}
      <g className="zzz" fill="var(--navy)" fontSize="18" fontStyle="italic">
        <text x="168" y="62">z</text>
        <text x="180" y="46" fontSize="14">z</text>
        <text x="190" y="34" fontSize="11">z</text>
      </g>
      <g className="hearts" fill="var(--heart)">
        <path d="M172 52 q-6 -8 -12 0 q-4 7 12 16 q16 -9 12 -16 q-6 -8 -12 0z" transform="scale(0.6) translate(120 10)" />
        <path d="M172 52 q-6 -8 -12 0 q-4 7 12 16 q16 -9 12 -16 q-6 -8 -12 0z" transform="scale(0.45) translate(-30 60)" />
      </g>
    </svg>
  );
}
