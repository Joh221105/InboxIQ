export function UspsLogo({ className = "size-8" }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 32 32" role="img" aria-label="USPS logo">
      <rect width="32" height="32" rx="8" fill="#FFFFFF" />
      <path d="M6 12h18l-4 3h6l-8 6H6l7-5H6v-4Z" fill="#004B87" />
      <path d="M7 9h20l-3 2H7V9Z" fill="#DA291C" />
    </svg>
  );
}
