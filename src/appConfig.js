export const MODEL_VERSION = 'v4.8.2'
export const ENVIRONMENT = 'Production'

export const ROLES = ['Analyst', 'Risk Engineer', 'Compliance']

export const ROLE_HOME = {
  Analyst: '/',
  'Risk Engineer': '/',
  Compliance: '/',
}

export const NAV_ITEMS = [
  { label: 'Overview', path: '/', roles: ROLES },
  { label: 'Review queue', path: '/review', roles: ROLES },
  { label: 'Drift monitoring', path: '/drift', roles: ['Risk Engineer', 'Compliance'] },
  { label: 'Policies', path: '/policies', roles: ['Risk Engineer', 'Compliance'], visibleRoles: ['Risk Engineer', 'Compliance'] },
  { label: 'Audit log', path: '/audit', roles: ['Compliance'], visibleRoles: ['Compliance'] },
]

export const ROUTE_ROLES = {
  '/': ROLES,
  '/review': ROLES,
  '/drift': ['Risk Engineer', 'Compliance'],
  '/policies': ['Risk Engineer', 'Compliance'],
  '/audit': ['Compliance'],
}

export function canAccessRoute(role, path) {
  return ROUTE_ROLES[path]?.includes(role) ?? false
}

export function getDefaultRoute(role) {
  return ROLE_HOME[role] ?? '/'
}