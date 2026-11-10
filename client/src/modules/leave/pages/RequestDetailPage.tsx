import { Card, Container, Stack, Text } from "@mantine/core";

import { PageHeader } from "../../../ui/components/PageHeader";

export default function RequestDetailPage() {
  return (
    <Container size="xl">
      <PageHeader
        title="Leave Request"
        subtitle="Review request details and available workflow actions"
      />
      <Card padding="lg">
        <Stack gap="xs">
          <Text fw={600}>Request details</Text>
          <Text size="sm" c="dimmed">
            Request details and action history are supplied by the Leave API.
          </Text>
        </Stack>
      </Card>
    </Container>
  );
}
