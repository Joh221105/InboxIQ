export function FedExLogo({ className = "size-8" }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 32 32" role="img" aria-label="FedEx logo">
      <rect width="32" height="32" rx="8" fill="#F8FAFC" />
      <text x="4" y="20.5" fontFamily="Arial, sans-serif" fontSize="10" fontWeight="800" fill="#4D148C">
        Fed
      </text>
      <text x="18" y="20.5" fontFamily="Arial, sans-serif" fontSize="10" fontWeight="800" fill="#FF6600">
        Ex
      </text>
    </svg>
  );
}
