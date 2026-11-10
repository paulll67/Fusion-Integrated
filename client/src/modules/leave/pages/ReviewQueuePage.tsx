import { Card, Container, Stack, Text } from "@mantine/core";

import { PageHeader } from "../../../ui/components/PageHeader";

export default function ReviewQueuePage() {
  return (
    <Container size="xl">
      <PageHeader
        title="Leave Review Queue"
        subtitle="Review assigned substitute and approval tasks"
      />
      <Card padding="lg">
        <Stack gap="xs">
          <Text fw={600}>Assigned tasks</Text>
          <Text size="sm" c="dimmed">
            Assigned Leave workflow tasks are supplied by the Leave API.
          </Text>
        </Stack>
      </Card>
    </Container>
  );
}
