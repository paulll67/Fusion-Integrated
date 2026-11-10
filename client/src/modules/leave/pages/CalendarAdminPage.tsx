import { Card, Container, Stack, Text } from "@mantine/core";

import { PageHeader } from "../../../ui/components/PageHeader";

export default function CalendarAdminPage() {
  return (
    <Container size="xl">
      <PageHeader title="Holiday and Restricted Holiday Calendar" subtitle="Maintain the currently published leave calendar" />
      <Card padding="lg">
        <Stack gap="xs">
          <Text fw={600}>Calendar administration</Text>
          <Text size="sm" c="dimmed">Published calendar data is supplied by the Leave API.</Text>
        </Stack>
      </Card>
    </Container>
  );
}
