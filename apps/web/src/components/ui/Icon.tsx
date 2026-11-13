import type { CSSProperties, ReactNode } from 'react'

// Ícones de traço 1.8 em 24x24 (os mesmos do template/app.js).
const PATHS = {
    grid: (
        <>
            <rect x="3" y="3" width="7" height="7" rx="1.5" />
            <rect x="14" y="3" width="7" height="7" rx="1.5" />
            <rect x="3" y="14" width="7" height="7" rx="1.5" />
            <rect x="14" y="14" width="7" height="7" rx="1.5" />
        </>
    ),
    users: (
        <>
            <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
            <circle cx="9" cy="7" r="4" />
            <path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75" />
        </>
    ),
    key: (
        <>
            <circle cx="7.5" cy="15.5" r="4.5" />
            <path d="m10.7 12.3 9.8-9.8M17 6l3 3M14 9l2 2" />
        </>
    ),
    db: (
        <>
            <ellipse cx="12" cy="5" rx="8" ry="3" />
            <path d="M4 5v14c0 1.7 3.6 3 8 3s8-1.3 8-3V5" />
            <path d="M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3" />
        </>
    ),
    history: (
        <>
            <path d="M3 12a9 9 0 1 0 3-6.7L3 8" />
            <path d="M3 3v5h5M12 7v5l3 2" />
        </>
    ),
    search: (
        <>
            <circle cx="11" cy="11" r="7" />
            <path d="m20 20-3.5-3.5" />
        </>
    ),
    bell: (
        <>
            <path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9" />
            <path d="M10.3 21a1.94 1.94 0 0 0 3.4 0" />
        </>
    ),
    alert: (
        <>
            <path d="m21.7 18-8-14a2 2 0 0 0-3.4 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.7-3Z" />
            <path d="M12 9v4M12 17h.01" />
        </>
    ),
    info: (
        <>
            <circle cx="12" cy="12" r="9" />
            <path d="M12 16v-4M12 8h.01" />
        </>
    ),
    menu: <path d="M4 6h16M4 12h16M4 18h16" />,
    lock: (
        <>
            <rect x="4" y="11" width="16" height="10" rx="2" />
            <path d="M8 11V7a4 4 0 0 1 8 0v4" />
        </>
    ),
    inbox: (
        <>
            <path d="M22 12h-6l-2 3h-4l-2-3H2" />
            <path d="M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11Z" />
        </>
    ),
    arrowLeft: <path d="M19 12H5M12 19l-7-7 7-7" />,
    arrowRight: <path d="M5 12h14M12 5l7 7-7 7" />,
    mail: (
        <>
            <rect x="3" y="5" width="18" height="14" rx="2" />
            <path d="M3.5 6.5 12 13l8.5-6.5" />
        </>
    ),
    eye: (
        <>
            <path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12z" />
            <circle cx="12" cy="12" r="3" />
        </>
    ),
    eyeOff: (
        <>
            <path d="M10.6 5.6A9.8 9.8 0 0 1 12 5.5c6 0 9.5 6.5 9.5 6.5a17 17 0 0 1-2.7 3.4M6.3 6.9A16.7 16.7 0 0 0 2.5 12S6 18.5 12 18.5a9.4 9.4 0 0 0 4.4-1.1" />
            <path d="M9.9 9.9a3 3 0 0 0 4.2 4.2M3 3l18 18" />
        </>
    ),
    logout: <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9" />,
    star: <path d="M12 3.5l2.6 5.3 5.9.9-4.3 4.1 1 5.8L12 16.9l-5.2 2.7 1-5.8-4.3-4.1 5.9-.9z" />,
    shield: (
        <>
            <path d="M12 3l7 3v5c0 4.5-3 8-7 10-4-2-7-5.5-7-10V6l7-3z" />
            <path d="M9.5 12l2 2 3.5-3.5" />
        </>
    ),
    plug: (
        <>
            <path d="M9 7V3M15 7V3" />
            <path d="M6 7h12v4a6 6 0 0 1-12 0V7z" />
            <path d="M12 17v4" />
        </>
    ),
    clock: (
        <>
            <circle cx="12" cy="12" r="9" />
            <path d="M12 7v5l3 2" />
        </>
    ),
    receipt: (
        <>
            <path d="M6 3h12v18l-3-2-3 2-3-2-3 2V3z" />
            <path d="M9 8h6M9 12h6" />
        </>
    ),
    building: (
        <>
            <path d="M4 21V5a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v16" />
            <path d="M16 9h2a2 2 0 0 1 2 2v10" />
            <path d="M8 7h4M8 11h4M8 15h4M3 21h18" />
        </>
    ),
    plus: <path d="M12 5v14M5 12h14" />,
    check: <path d="M5 12.5l4.5 4.5L19 7" />,
    download: <path d="M12 4v11M7 10l5 5 5-5M5 20h14" />,
    chevrons: <path d="M8 9l4-4 4 4M8 15l4 4 4-4" />,
    close: <path d="M6 6l12 12M18 6L6 18" />,
    flow: (
        <>
            <path d="M20 11a8 8 0 0 0-14.5-4.5L4 8" />
            <path d="M4 4v4h4" />
            <path d="M4 13a8 8 0 0 0 14.5 4.5L20 16" />
            <path d="M20 20v-4h-4" />
        </>
    ),
    sheet: (
        <>
            <rect x="4" y="4" width="16" height="16" rx="2" />
            <path d="M4 10h16M10 4v16" />
        </>
    ),
    calendar: (
        <>
            <rect x="3.5" y="5" width="17" height="15" rx="2" />
            <path d="M8 3v4M16 3v4M3.5 10h17" />
        </>
    ),
    filter: <path d="M4 5h16l-6 8v6l-4-2v-4L4 5z" />,
    // Documentação (menu) e ícones das páginas de documentação
    book: (
        <>
            <path d="M4 19.5V5a2 2 0 0 1 2-2h13v15H6.5A2.5 2.5 0 0 0 4 20.5 2.5 2.5 0 0 0 6.5 23H19v-5" />
            <path d="M8 7h7" />
        </>
    ),
    fileText: (
        <>
            <path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z" />
            <path d="M14 3v6h6M8 13h8M8 17h6" />
        </>
    ),
    trendingUp: <path d="M3 17l6-6 4 4 8-8M15 7h6v6" />,
    barChart: <path d="M4 20V10M10 20V4M16 20v-7M22 20H2" />,
    xCircle: (
        <>
            <circle cx="12" cy="12" r="9" />
            <path d="M15 9l-6 6M9 9l6 6" />
        </>
    ),
    dollar: (
        <path d="M12 2v20M17 6.5C17 4.6 14.8 3.5 12 3.5S7 4.7 7 7s2.2 3.2 5 3.8 5 1.6 5 4-2.2 3.7-5 3.7-5-1.2-5-3.2" />
    ),
    percent: (
        <>
            <path d="M19 5L5 19" />
            <circle cx="6.5" cy="6.5" r="2.5" />
            <circle cx="17.5" cy="17.5" r="2.5" />
        </>
    ),
    pieChart: (
        <>
            <path d="M21 12A9 9 0 1 1 12 3v9z" />
            <path d="M21 12a9 9 0 0 0-9-9" />
        </>
    ),
    scale: (
        <>
            <path d="M12 3v18M7 21h10M5 7h14" />
            <path d="M5 7l-3 7a3.5 3.5 0 0 0 6 0zM19 7l-3 7a3.5 3.5 0 0 0 6 0z" />
        </>
    ),
    target: (
        <>
            <circle cx="12" cy="12" r="9" />
            <circle cx="12" cy="12" r="5" />
            <circle cx="12" cy="12" r="1" />
        </>
    ),
    ban: (
        <>
            <circle cx="12" cy="12" r="9" />
            <path d="M5.7 5.7l12.6 12.6" />
        </>
    ),
    sun: (
        <>
            <circle cx="12" cy="12" r="4" />
            <path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
        </>
    ),
    moon: <path d="M20.5 14.5A8.5 8.5 0 1 1 9.5 3.5a7 7 0 0 0 11 11z" />,
} satisfies Record<string, ReactNode>

export type IconName = keyof typeof PATHS

type IconProps = {
    name: IconName
    size?: number
    style?: CSSProperties
}

export function Icon({ name, size = 18, style }: IconProps) {
    return (
        <svg
            width={size}
            height={size}
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth={1.8}
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
            style={style}
        >
            {PATHS[name]}
        </svg>
    )
}
