/* Bun — InboxIQ's rabbit mascot. Flat vector, 3–4 fills, viewBox 0 0 80 100.
   Built from the InboxIQ design-system spec exactly. */

const FUR    = "#F5EDD8";
const INNER  = "#E8C4B8";
const EYE    = "#2D2011";
const NOSE   = "#C49080";
const SHADE  = "#C8B89A";
const ENV    = "#F0D080";
const ENV_LINE = "#C8A840";

type BunExpr = "default" | "empty" | "loading" | "error";

interface BunProps {
  size?: number;
  expr?: BunExpr;
  envelope?: boolean;
  bob?: boolean;
  className?: string;
  style?: React.CSSProperties;
  label?: string;
}

export function Bun({
  size = 120,
  expr = "default",
  envelope = true,
  bob = false,
  className = "",
  style = {},
  label = "Bun, the InboxIQ rabbit",
}: BunProps) {
  const isLoading = expr === "loading";
  const isEmpty   = expr === "empty";
  const isError   = expr === "error";
  const doBob = bob || isLoading;

  const leftEarTilt  = isEmpty ? -20 : -7;
  const rightEarTilt = isEmpty ?  20 :  7;

  return (
    <svg
      role="img"
      aria-label={label}
      width={size * 0.8}
      height={size}
      viewBox="0 0 80 100"
      className={className}
      style={{ display: "block", overflow: "visible", ...style }}
    >
      <title>{label}</title>

      {/* ears */}
      <g className={doBob ? "bun-bob-ears" : ""}>
        {isError ? (
          /* folded left ear on error */
          <g transform="rotate(34 30 30)">
            <rect x="24" y="14" width="11" height="22" rx="5.5" fill={FUR} />
            <rect x="27" y="17" width="5"  height="15" rx="2.5" fill={INNER} />
            <path d="M24 22 q6 -3 11 0" stroke={SHADE} strokeWidth="1.2" fill="none" opacity="0.5" />
          </g>
        ) : (
          <g transform={`rotate(${leftEarTilt} 30 34)`}>
            <rect x="24.5" y="2"  width="11" height="34" rx="5.5" fill={FUR} />
            <rect x="27.5" y="6"  width="5"  height="25" rx="2.5" fill={INNER} />
          </g>
        )}
        <g transform={`rotate(${rightEarTilt} 50 34)`}>
          <rect x="44.5" y="2"  width="11" height="34" rx="5.5" fill={FUR} />
          <rect x="47.5" y="6"  width="5"  height="25" rx="2.5" fill={INNER} />
        </g>
      </g>

      {/* body */}
      <ellipse cx="40" cy="70" rx="26" ry="27" fill={FUR} />
      <ellipse cx="40" cy="84" rx="24" ry="13" fill={SHADE} opacity="0.30" />

      {/* head */}
      <circle cx="40" cy="44" r="20" fill={FUR} />
      <ellipse cx="40" cy="55" rx="17" ry="8"  fill={SHADE} opacity="0.22" />

      {/* eyes */}
      <circle cx="32.5" cy="43" r="2.4" fill={EYE} />
      <circle cx="47.5" cy="43" r="2.4" fill={EYE} />
      {/* catchlights */}
      <circle cx="33.3" cy="42.2" r="0.7" fill="#fff" opacity="0.85" />
      <circle cx="48.3" cy="42.2" r="0.7" fill="#fff" opacity="0.85" />
      {/* nose */}
      <ellipse cx="40" cy="49.5" rx="1.9" ry="1.5" fill={NOSE} />

      {/* envelope */}
      {envelope && (
        <g>
          <ellipse cx="26" cy="76" rx="5" ry="6" fill={FUR} />
          <ellipse cx="54" cy="76" rx="5" ry="6" fill={FUR} />
          <rect x="26" y="66" width="28" height="19" rx="2.5" fill={ENV} />
          {isEmpty ? (
            <>
              <path d="M26 66 L40 60 L54 66" fill="none" stroke={ENV_LINE} strokeWidth="1.4" strokeLinejoin="round" />
              <path d="M26 66 L40 74 L54 66" fill="none" stroke={ENV_LINE} strokeWidth="1.2" opacity="0.7" />
            </>
          ) : (
            <path d="M26 66 L40 76 L54 66" fill="none" stroke={ENV_LINE} strokeWidth="1.4" strokeLinejoin="round" />
          )}
        </g>
      )}
    </svg>
  );
}
