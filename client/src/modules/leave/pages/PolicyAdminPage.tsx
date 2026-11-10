import { Card, Container, Stack, Text } from "@mantine/core";

import { PageHeader } from "../../../ui/components/PageHeader";

export default function PolicyAdminPage() {
  return (
    <Container size="xl">
      <PageHeader
        title="Leave Policy Configuration"
        subtitle="Manage the current leave entitlements and counting rules"
      />
      <Card padding="lg">
        <Stack gap="xs">
          <Text fw={600}>Policy administration</Text>
          <Text size="sm" c="dimmed">
            Current policy parameters are managed by authorized administrators.
          </Text>
        </Stack>
      </Card>
    </Container>
  );
}
