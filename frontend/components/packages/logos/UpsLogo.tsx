export function UpsLogo({ className = "size-8" }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 32 32" role="img" aria-label="UPS logo">
      <path d="M7 5h18v11c0 5.7-3.5 9.8-9 11.5C10.5 25.8 7 21.7 7 16V5Z" fill="#351C15" />
      <path d="M10 8h12v8c0 3.7-2.2 6.4-6 7.8-3.8-1.4-6-4.1-6-7.8V8Z" fill="#7A4B22" />
      <text x="10.2" y="17.7" fontFamily="Arial, sans-serif" fontSize="7.5" fontWeight="800" fill="#FACC15">
        UPS
      </text>
    </svg>
  );
}
