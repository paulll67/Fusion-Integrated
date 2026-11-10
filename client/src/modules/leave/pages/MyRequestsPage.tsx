import { Card, Container, Stack, Text } from "@mantine/core";

import { PageHeader } from "../../../ui/components/PageHeader";

export default function MyRequestsPage() {
  return (
    <Container size="xl">
      <PageHeader title="My Leave Requests" subtitle="Track submitted leave applications and action history" />
      <Card padding="lg">
        <Stack gap="xs">
          <Text fw={600}>Requests</Text>
          <Text size="sm" c="dimmed">Request data is supplied by the Leave API.</Text>
        </Stack>
      </Card>
    </Container>
  );
}
