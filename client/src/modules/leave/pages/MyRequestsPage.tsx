import { useState } from "react";
import {
  ActionIcon,
  Button,
  Card,
  Container,
  Group,
  Stack,
  Text,
} from "@mantine/core";
import { notifications } from "@mantine/notifications";
import { FaHistory, FaUserCheck } from "react-icons/fa";

import { errorMessage } from "../../../lib/http";
import { DataTable } from "../../../ui/components/DataTable";
import { ErrorState } from "../../../ui/components/ErrorState";
import { PageHeader } from "../../../ui/components/PageHeader";
import { StatusBadge } from "../../../ui/components/StatusBadge";
import { HistoryDrawer } from "../components/HistoryDrawer";
import { useLeaveRequests, useTransition } from "../api/hooks";
import type { LeaveRequest } from "../api/types";

export default function MyRequestsPage() {
  const { data, isPending, error } = useLeaveRequests();
  const transition = useTransition();
  const [historyFor, setHistoryFor] = useState<number | null>(null);

  if (error) return <Container size="xl"><ErrorState error={error} /></Container>;

  function withdraw(app: LeaveRequest) {
    transition.mutate(
      { id: app.id, to_status: "withdrawn", reason: "Withdrawn by the employee" },
      {
        onSuccess: () => notifications.show({
          color: "gray", title: "Withdrawn",
          message: `Your leave request has been withdrawn.`,
        }),
        onError: (e) => notifications.show({
          color: "red", title: "Could not withdraw", message: errorMessage(e),
        }),
      },
    );
  }

  return (
    <Container size="xl">
      <PageHeader
        title="My Requests"
        subtitle="Your leave applications and their current status"
      />
      <Card padding="lg">
        <DataTable<LeaveRequest>
          rows={(data?.results ?? []) as LeaveRequest[]}
          loading={isPending}
          rowKey={(r) => r.id}
          minWidth={900}
          columns={[
            {
              key: "category", header: "Category",
              render: (r) => (
                <Stack gap={0}>
                  <Text fw={600}>{r.category}</Text>
                  {r.station_leave_details && (
                    <Text size="xs" c="dimmed">
                      Station Leave: {r.station_leave_details?.station_name || "N/A"}
                    </Text>
                  )}
                </Stack>
              ),
            },
            {
              key: "period", header: "Period",
              render: (r) => (
                <Stack gap={0}>
                  <Text size="sm">{new Date(r.start_date).toLocaleDateString()}</Text>
                  <Text size="sm">to {new Date(r.end_date).toLocaleDateString()}</Text>
                </Stack>
              ),
            },
            {
              key: "status", header: "Status",
              render: (r) => (
                <StatusBadge status={r.status} />
              ),
            },
            {
              key: "submitted_at", header: "Submitted",
              render: (r) => r.submitted_at
                ? new Date(r.submitted_at).toLocaleDateString() : "—",
            },
            {
              key: "actions", header: "Actions",
              render: (r) => (
                <Group>
                  <ActionIcon size="xs" onClick={() => setHistoryFor(r.id)}>
                    <FaHistory />
                  </ActionIcon>
                  {r.status !== "approved" && r.status !== "rejected" && (
                    <Button
                      size="xs"
                      color="red"
                      onClick={() => withdraw(r)}
                      disabled={r.status === "withdrawn"}
                    >
                      Withdraw
                    </Button>
                  )}
                </Group>
              ),
            },
          ]}
        />
      </Card>
      {historyFor !== null && (
        <HistoryDrawer requestId={historyFor} onClose={() => setHistoryFor(null)} />
      )}
    </Container>
  );
}
