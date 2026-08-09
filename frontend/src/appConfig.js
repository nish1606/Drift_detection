export const MODEL_VERSION = 'v4.8.2'
export const ENVIRONMENT = 'Production'

export const ROLES = ['Analyst', 'RiskEngineer', 'Compliance']

export const ROLE_HOME = {
  Analyst: '/',
  RiskEngineer: '/',
  Compliance: '/',
}

export const NAV_ITEMS = [
  { label: 'Overview', path: '/', roles: ROLES },
  { label: 'Review queue', path: '/review', roles: ROLES },
  { label: 'Drift monitoring', path: '/drift', roles: ['RiskEngineer', 'Compliance'] },
  { label: 'Model explainability', path: '/explainability', roles: ['RiskEngineer', 'Compliance'] },
  { label: 'Fairness monitoring', path: '/fairness', roles: ['RiskEngineer', 'Compliance'] },
  { label: 'Policies', path: '/policies', roles: ROLES, visibleRoles: ROLES },
  { label: 'Audit log', path: '/audit', roles: ['Compliance'], visibleRoles: ['Compliance'] },
]

export const ROUTE_ROLES = {
  '/': ROLES,
  '/review': ROLES,
  '/drift': ['RiskEngineer', 'Compliance'],
  '/explainability': ['RiskEngineer', 'Compliance'],
  '/fairness': ['RiskEngineer', 'Compliance'],
  '/policies': ROLES,
  '/audit': ['Compliance'],
}

export function canAccessRoute(role, path) {
  return ROUTE_ROLES[path]?.includes(role) ?? false
}

export function getDefaultRoute(role) {
  return ROLE_HOME[role] ?? '/'
}