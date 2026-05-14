export function AmazonLogo({ className = "size-8" }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 32 32" role="img" aria-label="Amazon logo">
      <rect width="32" height="32" rx="8" fill="#111827" />
      <path
        d="M9 19c4.5 3.5 9.5 3.7 14.8.4"
        fill="none"
        stroke="#FF9900"
        strokeLinecap="round"
        strokeWidth="2.8"
      />
      <path d="M22.5 18.2l3.1.2-1.7 2.6" fill="none" stroke="#FF9900" strokeLinecap="round" strokeWidth="2" />
    </svg>
  );
}
