import {
  Alert,
  Badge,
  Button,
  Card,
  Container,
  Group,
  Paper,
  SimpleGrid,
  Stack,
  Table,
  Text,
  Tooltip,
} from "@mantine/core";
import { notifications } from "@mantine/notifications";
import { FaCalendarAlt, FaDownload, FaHistory, FaInfoCircle } from "react-icons/fa";

import { useAuth } from "../../../auth/AuthProvider";
import { errorMessage } from "../../../lib/http";
import { ErrorState } from "../../../ui/components/ErrorState";
import { PageHeader } from "../../../ui/components/PageHeader";
import {
  useLeaveBalances,
  useLeaveHistory,
  type LeaveBalanceItem,
  type LeaveHistoryItem,
} from "../api/hooks";

/**
 * BalancesPage.tsx
 * 
 * Implements EL-UC-012: View Leave Balances and History.
 * Displays current leave balances (CL, RH, SCL, EL, COL, VL) and historical request status.
 * Accessible only to authenticated employees for their own records.
 */
function BalancesPage() {
  const { user } = useAuth();

  // Hooks for data fetching
  const balancesData = useLeaveBalances();
  const historyData = useLeaveHistory();

  // Derived state
  const balances = balancesData?.data ?? [];
  const history = historyData?.data ?? [];
  const isPending = balancesData.isPending || historyData.isPending;
  const error = balancesData.error || historyData.error;

  // Helper to determine badge color based on balance type and value
  const getBalanceColor = (type: string, amount: number) => {
    if (amount < 0) return "red";
    if (type === "CL" || type === "RH") return "blue";
    if (type === "EL" || type === "COL" || type === "VL") return "green";
    return "gray";
  };

  // Helper to format currency or days
  const formatValue = (value: number, type: string) => {
    if (type.includes("DAYS")) {
      return `${value} Days`;
    }
    return value.toString();
  };

  return (
    <Container size="xl">
      <PageHeader title="Leave Balances & History" />

      {/* Access Control Alert */}
      {!user && (
        <Alert color="warning" icon={<FaInfoCircle />}>\nPlease log in to view your leave balances and history.\n</Alert>
      )}

      {/* Error State */}
      {error && (
        <ErrorState message={errorMessage(error)} />
      )}

      {!isPending && !error && (balances.length === 0 || history.length === 0) && (
        <Card padding="lg">
          <Text size="sm" c="dimmed">
            No leave balances or history records found for this period.
          </Text>
        </Card>
      )}

      {/* Balances Section */}
      {balances.length > 0 && (
        <Card padding="lg" mb="md">
          <Group justify="space-between" mb="xs">
            <div>
              <Text fw={600}>Current Leave Balances</Text>
              <Text size="xs" c="dimmed">
                Your available leave entitlements as of today.
              </Text>
            </div>
            <Badge variant="light" color="blue">
              {balances.length} Categories
            </Badge>
          </Group>

          <SimpleGrid cols={2} gap="md">
            {balances.map((item) => (
              <Paper key={item.id} withBorder radius="sm" p="sm">
                <Stack justify="space-between" h="100%">
                  <div>
                    <Text fw={600} size="lg">
                      {item.category}
                    </Text>
                    <Text size="xs" c="dimmed">
                      {formatValue(item.available, item.category)}
                    </Text>
                  </div>
                  <Badge
                    variant="light"
                    color={getBalanceColor(item.category, item.available)}
                  >
                    {item.available}
                  </Badge>
                </Stack>
              </Paper>
            ))}
          </SimpleGrid>
        </Card>
      )}

      {/* History Section */}
      {history.length > 0 && (
        <Card padding="lg">
          <Group justify="space-between" mb="xs">
            <div>
              <Text fw={600}>Leave Request History</Text>
              <Text size="xs" c="dimmed">
                Past applications, decisions, and resumption records.
              </Text>
            </div>
            <Button
              variant="default"
              size="xs"
              leftSection={<FaDownload size={12} />}
              onClick={() => notifications.show({
                title: "Export functionality coming soon",
                message: "Full CSV export of history is under development.",
                color: "blue",
              })}
            >
              Export
            </Button>
          </Group>

          <Table striped highlightOnHover withBorder>
            <thead>
              <tr>
                <th>Date</th>
                <th>Category</th>
                <th>Type</th>
                <th>Status</th>
                <th>Decision/Outcome</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {history.map((item) => (
                <tr key={item.id}>
                  <td>{new Date(item.date).toLocaleDateString()}</td>
                  <td>
                    <Badge color="blue">{item.category}</Badge>
                  </td>
                  <td>{item.type}</td>
                  <td>
                    {item.status === "APPROVED" && <Badge color="green">Approved</Badge>}
                    {item.status === "REJECTED" && <Badge color="red">Rejected</Badge>}
                    {item.status === "CANCELLED" && <Badge color="orange">Cancelled</Badge>}
                    {item.status === "PENDING" && <Badge color="gray">Pending</Badge>}
                  </td>
                  <td>{item.decision || item.outcome || "N/A"}</td>
                  <td>
                    <Tooltip label={item.id.toString()}>
                      <Button
                        variant="outline"
                        size="xs"
                        component="a"
                        href={`#/request/${item.id}`}
                      >
                        View
                      </Button>
                    </Tooltip>
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>
        </Card>
      )}

      {/* Info Note */}
      <Paper withBorder radius="sm" p="md">
        <Text size="sm" c="dimmed">
          <strong>Note:</strong> Balances are updated in real-time upon approval or adjustment. 
          Historical records reflect the final state at the time of decision.
        </Text>
      </Paper>
    </Container>
  );
}

export default BalancesPage;
