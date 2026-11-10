import { Card, Container, Stack, Text } from "@mantine/core";

import { PageHeader } from "../../../ui/components/PageHeader";

export default function RecordsAdminPage() {
  return (
    <Container size="xl">
      <PageHeader title="Leave Records Maintenance" subtitle="Maintain authorized offline-sanctioned leave records" />
      <Card padding="lg">
        <Stack gap="xs">
          <Text fw={600}>Records administration</Text>
          <Text size="sm" c="dimmed">Authorized record data is supplied by the Leave API.</Text>
        </Stack>
      </Card>
    </Container>
  );
}
