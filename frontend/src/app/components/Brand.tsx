interface BrandProps {
  size?: 'sm' | 'md' | 'lg';
}

export function Brand({ size = 'md' }: BrandProps) {
  const dims = {
    sm: { svg: 28, text: 'text-lg' },
    md: { svg: 36, text: 'text-2xl' },
    lg: { svg: 56, text: 'text-4xl' },
  }[size];

  return (
    <div className="flex items-center gap-3 select-none">
      <svg
        width={dims.svg}
        height={dims.svg}
        viewBox="0 0 64 64"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="navio-palm"
        aria-hidden="true"
      >
        <defs>
          <linearGradient id="trunk" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#a16939" />
            <stop offset="100%" stopColor="#7a4a26" />
          </linearGradient>
          <linearGradient id="frond" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#3da673" />
            <stop offset="100%" stopColor="#206b48" />
          </linearGradient>
        </defs>

        <circle cx="42" cy="58" r="6" fill="#f0c674" opacity="0.45" />

        <path
          d="M30 60 C 28 48, 28 36, 30 22 L 34 22 C 36 36, 36 48, 34 60 Z"
          fill="url(#trunk)"
        />
        <path d="M30 36 L 34 36 M 30 44 L 34 44 M 30 52 L 34 52" stroke="#5a3a20" strokeWidth="0.6" />

        <g className="navio-fronds" style={{ transformOrigin: '32px 22px' }}>
          <path
            d="M32 22 C 22 18, 12 18, 4 22 C 14 22, 24 22, 32 22 Z"
            fill="url(#frond)"
          />
          <path
            d="M32 22 C 42 18, 52 18, 60 22 C 50 22, 40 22, 32 22 Z"
            fill="url(#frond)"
          />
          <path
            d="M32 22 C 24 12, 14 8, 6 8 C 16 14, 24 20, 32 22 Z"
            fill="url(#frond)"
          />
          <path
            d="M32 22 C 40 12, 50 8, 58 8 C 48 14, 40 20, 32 22 Z"
            fill="url(#frond)"
          />
          <path
            d="M32 22 C 28 14, 24 6, 22 0 C 28 8, 32 16, 32 22 Z"
            fill="url(#frond)"
          />
          <path
            d="M32 22 C 36 14, 40 6, 42 0 C 36 8, 32 16, 32 22 Z"
            fill="url(#frond)"
          />
          <circle cx="29" cy="20" r="1.6" fill="#c97a3a" />
          <circle cx="32" cy="19" r="1.6" fill="#c97a3a" />
          <circle cx="35" cy="20" r="1.6" fill="#c97a3a" />
        </g>
      </svg>

      <span
        className={`${dims.text} font-medium tracking-tight text-foreground`}
        style={{ fontFamily: 'Georgia, "Times New Roman", serif', letterSpacing: '0.02em' }}
      >
        Navio
      </span>

      <style>{`
        @keyframes navio-sway {
          0%, 100% { transform: rotate(-4deg); }
          50%      { transform: rotate(4deg); }
        }
        @keyframes navio-bob {
          0%, 100% { transform: translateY(0); }
          50%      { transform: translateY(-1px); }
        }
        .navio-palm {
          animation: navio-bob 4s ease-in-out infinite;
        }
        .navio-fronds {
          animation: navio-sway 3.5s ease-in-out infinite;
        }
      `}</style>
    </div>
  );
}
