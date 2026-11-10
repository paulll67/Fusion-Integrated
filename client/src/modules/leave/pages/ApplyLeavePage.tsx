import { Card, Container, Stack, Text } from "@mantine/core";

import { PageHeader } from "../../../ui/components/PageHeader";

export default function ApplyLeavePage() {
  return (
    <Container size="xl">
      <PageHeader
        title="Apply for Leave"
        subtitle="Submit a leave application with dates, category, and supporting details"
      />
      <Card padding="lg">
        <Stack gap="xs">
          <Text fw={600}>Leave application</Text>
          <Text size="sm" c="dimmed">
            Leave application fields are supplied by the Leave API.
          </Text>
        </Stack>
      </Card>
    </Container>
  );
}
