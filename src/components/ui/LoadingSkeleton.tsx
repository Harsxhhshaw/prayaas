interface LoadingSkeletonProps {
  variant?: 'text' | 'card' | 'metric' | 'map';
  count?: number;
}

function SkeletonPulse({ className = '' }: { className?: string }) {
  return <div className={`animate-pulse bg-navy-700/50 rounded ${className}`} />;
}

export function LoadingSkeleton({ variant = 'text', count = 1 }: LoadingSkeletonProps) {
  const items = Array.from({ length: count }, (_, i) => i);

  if (variant === 'metric') {
    return (
      <div className="grid grid-cols-6 gap-3">
        {items.map((i) => (
          <div key={i} className="bg-surface-secondary border border-border-primary rounded-lg p-4">
            <SkeletonPulse className="h-3 w-24 mb-3" />
            <SkeletonPulse className="h-7 w-16 mb-2" />
            <SkeletonPulse className="h-3 w-20" />
          </div>
        ))}
      </div>
    );
  }

  if (variant === 'card') {
    return (
      <div className="space-y-3">
        {items.map((i) => (
          <div key={i} className="bg-surface-secondary border border-border-primary rounded-lg p-4">
            <SkeletonPulse className="h-4 w-32 mb-3" />
            <SkeletonPulse className="h-3 w-full mb-2" />
            <SkeletonPulse className="h-3 w-3/4" />
          </div>
        ))}
      </div>
    );
  }

  if (variant === 'map') {
    return (
      <div className="bg-surface-secondary border border-border-primary rounded-lg overflow-hidden">
        <SkeletonPulse className="h-[500px] w-full rounded-none" />
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {items.map((i) => (
        <SkeletonPulse key={i} className="h-4 w-full" />
      ))}
    </div>
  );
}
