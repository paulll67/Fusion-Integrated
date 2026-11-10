/** Shared query-key namespace for the Leave module. */
export const keys = {
  requests: (filters?: unknown) => ["leave", "requests", filters] as const,
  request: (id: number) => ["leave", "request", id] as const,
  tasks: (requestId?: number) => ["leave", "tasks", requestId] as const,
  accounts: (userId?: number) => ["leave", "accounts", userId] as const,
  policies: () => ["leave", "policies"] as const,
  hierarchy: () => ["leave", "hierarchy"] as const,
  calendars: () => ["leave", "calendars"] as const,
  sla: () => ["leave", "sla"] as const,
};
