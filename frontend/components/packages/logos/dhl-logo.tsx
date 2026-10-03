export function DhlLogo({ className = "size-8" }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 32 32" role="img" aria-label="DHL logo">
      <rect width="32" height="32" rx="8" fill="#FFCC00" />
      <path d="M5 11h22M5 21h22" stroke="#D40511" strokeWidth="1.8" />
      <text x="7" y="19" fontFamily="Arial, sans-serif" fontSize="10" fontWeight="900" fill="#D40511">
        DHL
      </text>
    </svg>
  );
}
