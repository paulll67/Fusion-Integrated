import { Card, Container, Stack, Text } from "@mantine/core";

import { PageHeader } from "../../../ui/components/PageHeader";

export default function BalancesPage() {
  return (
    <Container size="xl">
      <PageHeader title="Leave Balances" subtitle="View current leave balances and ledger history" />
      <Card padding="lg">
        <Stack gap="xs">
          <Text fw={600}>Balances</Text>
          <Text size="sm" c="dimmed">Leave account data is supplied by the Leave API.</Text>
        </Stack>
      </Card>
    </Container>
  );
}
