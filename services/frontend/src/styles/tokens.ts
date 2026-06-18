export const COLORS = {
  primary: '#648f8c',
  primaryHover: '#7aa8a5',
  primaryAlpha10: '#648f8c1a',
  primaryAlpha33: '#648f8c33',
  primaryAlpha39: 'rgba(100, 143, 140, 0.39)',

  bg: '#121212',
  bgDark: '#0d0d0d',
  surface: '#1e1e1e',
  surface2: '#1a1a1a',
  surface3: '#151515',

  border: '#333333',
  borderLight: '#252525',
  borderDark: '#222222',

  textPrimary: '#ffffff',
  textSecondary: '#aaaaaa',
  textMuted: '#666666',
  textDim: '#555555',

  success: '#a9dc76',
  warning: '#ffda6a',
  danger: '#ef4444',
  info: '#3b82f6',
  teal: '#10b981',
} as const;

export const RADII = {
  xs: '4px',
  sm: '6px',
  md: '8px',
  lg: '12px',
  xl: '16px',
  full: '9999px',
} as const;

export const FONT = {
  sans: "'Inter', 'Segoe UI', Roboto, sans-serif",
  mono: "'Courier New', Consolas, monospace",
} as const;

export const sharedStyles = {
  backBtn: {
    background: 'none',
    border: 'none',
    color: COLORS.primary,
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    fontSize: '14px',
    fontWeight: '500',
    flexShrink: 0,
  } satisfies React.CSSProperties,

  deployBtn: {
    backgroundColor: COLORS.primary,
    color: 'white',
    border: 'none',
    padding: '10px 20px',
    borderRadius: RADII.md,
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    fontWeight: 'bold',
    boxShadow: `0 4px 14px 0 ${COLORS.primaryAlpha39}`,
  } satisfies React.CSSProperties,

  card: {
    backgroundColor: COLORS.surface,
    padding: '15px',
    borderRadius: RADII.lg,
    border: `1px solid ${COLORS.border}`,
  } satisfies React.CSSProperties,

  cardTitle: {
    color: COLORS.primary,
    fontSize: '14px',
    marginBottom: '15px',
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    fontWeight: 'bold',
    margin: 0,
  } satisfies React.CSSProperties,

  selectInput: {
    backgroundColor: COLORS.bg,
    color: 'white',
    border: `1px solid ${COLORS.border}`,
    borderRadius: RADII.xs,
    padding: '2px 5px',
  } satisfies React.CSSProperties,

  badge: {
    backgroundColor: COLORS.primaryAlpha33,
    color: COLORS.primary,
    padding: '6px 15px',
    borderRadius: '20px',
    fontSize: '13px',
    border: `1px solid ${COLORS.primaryAlpha33}`,
    fontWeight: 'bold',
  } satisfies React.CSSProperties,

  infoRow: {
    display: 'flex',
    justifyContent: 'space-between',
    fontSize: '13px',
    color: COLORS.textSecondary,
    marginBottom: '5px',
  } satisfies React.CSSProperties,

  errorPage: {
    backgroundColor: COLORS.bg,
    color: 'white',
    minHeight: '100vh',
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center',
    alignItems: 'center',
    gap: '20px',
  } satisfies React.CSSProperties,

  pageContainer: {
    backgroundColor: COLORS.bg,
    color: 'white',
    padding: '20px',
    fontFamily: FONT.sans,
  } satisfies React.CSSProperties,
} as const;
