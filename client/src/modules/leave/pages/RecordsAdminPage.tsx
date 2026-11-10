import { useState } from "react";
import {
  Alert,
  Button,
  Card,
  Container,
  Group,
  NumberInput,
  Select,
  Stack,
  Text,
} from "@mantine/core";
import { notifications } from "@mantine/notifications";
import { FaInfoCircle, FaHistory } from "react-icons/fa";

import { errorMessage } from "../../../lib/http";
import { Field, FormRow, FormSection } from "../../../ui/components/FormSection";
import { PageHeader } from "../../../ui/components/PageHeader";
import {
  useLeaveRecords,
  useRecordMaintenance,
} from "../api/hooks";

// -- Constants --
const ROUTES = [
  { value: "offline-sanction", label: "Record Offline Sanctioned Leave" },
  { value: "record-maintenance", label: "Maintain Authorized Records" },
];

// -- Types --
type RouteType = typeof ROUTES[number]["value"];

/**
 * RecordsAdminPage.tsx
 *
 * Authorized UI for recording already-sanctioned offline leave and maintaining
 * leave records without performing sanction decisions.
 *
 * Scope: Implements EL-UC-016 (Record Already-Sanctioned Offline Leave) and
 * EL-UC-017 (Maintain Authorized Leave Records).
 * 
 * Constraints:
 * - Identity references are integer user_id values.
 * - Cross-module data access uses public contracts from modules.leave.contracts.
 * - No sanction decisions are made here; this is purely administrative recording/maintenance.
 */

export default function RecordsAdminPage() {
  const [route, setRoute] = useState<RouteType>("offline-sanction");
  const [userId, setUserId] = useState<string>("");
  const [reference, setReference] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [category, setCategory] = useState("CL"); // Default to Casual Leave
  const [reason, setReason] = useState("");

  // Hooks for API interactions
  const recordOfflineSanction = useRecordMaintenance(); // Reusing maintenance hook for offline sanction as per blueprint
  
  // Note: In a full implementation, these would be distinct hooks:
  // - useRecordOfflineSanction() for EL-UC-016
  // - useRecordMaintenance() for EL-UC-017
  // For this assignment, we map the maintenance endpoint to handle both based on route selection.

  const busy = recordOfflineSanction.isPending;
  const ready = Boolean(userId) && reference.trim().length > 0;

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!ready || !userId) return;

    const body = {
      employee_user_id: Number(userId),
      reference: reference.trim(),
      category,
      start_date: startDate,
      end_date: endDate,
      reason,
      is_offline_sanction: route === "offline-sanction",
    };

    const mutation = recordOfflineSanction.mutate(body, {
      onSuccess: (record) => {
        notifications.show({
          color: "green",
          title: "Record Updated",
          message: `Leave record for ${userId} has been synchronized/maintained.`,
        });
        setUserId("");
        setReference("");
        setStartDate("");
        setEndDate("");
        setReason("");
      },
      onError: (e) => {
        notifications.show({
          color: "red",
          title: "Could not complete",
          message: errorMessage(e),
        });
      },
    });
  }

  return (
    <Container size="md">
      <PageHeader
        title="Leave Records Administration"
        subtitle="Record offline sanctions and maintain authorized records"
      />

      <Alert variant="light" color="blue" icon={<FaInfoCircle />} mb="md">
        <Text size="sm">
          This page allows administrators to synchronize leave that was sanctioned
          through an offline/paper process (EL-UC-016) or to perform authorized
          record maintenance/corrections (EL-UC-017). No new sanction decisions
          are made here.
        </Text>
      </Alert>

      <Card padding="lg">
        <FormSection
          first title="Select Operation"
          hint="Choose the type of administrative action to perform."
        >
          <Stack gap="xs">
            {ROUTES.map((r) => (
              <Group key={r.value} value={r.value}>
                <Select
                  value={route}
                  onChange={(val) => setRoute(val as RouteType)}
                  data={ROUTES.map((r) => ({ label: r.label, value: r.value }))}
                  allowCustomValue={false}
                  required
                />
              </Group>
            ))}
          </Stack>
        </FormSection>

        <FormSection
          first title="Leave Details"
          hint="Enter the employee ID and leave details."
        >
          <Stack gap="md">
            <FormRow>
              <Field span={6}>
                <TextInput
                  label="Employee User ID"
                  value={userId}
                  onChange={(val) => setUserId(val)}
                  placeholder="e.g. 1001"
                  required
                />
              </Field>
            </FormRow>

            <FormRow>
              <Field span={6}>
                <TextInput
                  label="Sanction/Reference Number"
                  value={reference}
                  onChange={(val) => setReference(val)}
                  placeholder="e.g. OFFLINE-2024-001"
                  required
                />
              </Field>
            </FormRow>

            <FormRow>
              <Field span={6}>
                <Select
                  label="Leave Category"
                  value={category}
                  onChange={(val) => setCategory(val)}
                  data={[
                    { label: "Casual Leave (CL)", value: "CL" },
                    { label: "Half-Year Leave (HFL)", value: "HFL" },
                    { label: "Full-Year Leave (FYL)", value: "FYL" },
                    { label: "Sick Leave (SL)", value: "SL" },
                  ]}
                />
              </Field>
            </FormRow>

            <FormRow>
              <Field span={6}>
                <TextInput
                  label="Start Date"
                  type="date"
                  value={startDate}
                  onChange={(val) => setStartDate(val)}
                />
              </Field>
            </FormRow>

            <FormRow>
              <Field span={6}>
                <TextInput
                  label="End Date"
                  type="date"
                  value={endDate}
                  onChange={(val) => setEndDate(val)}
                />
              </Field>
            </FormRow>

            <FormRow>
              <Field span={12}>
                <TextInput
                  label="Reason / Evidence Description"
                  value={reason}
                  onChange={(val) => setReason(val)}
                  placeholder="Brief description of the offline sanction or maintenance reason."
                  maxLength={500}
                />
              </Field>
            </FormRow>
          </Stack>
        </FormSection>

        <FormSection first title="Actions">
          <Button
            type="button"
            onClick={handleSubmit}
            disabled={!ready || busy}
            fullWidth
            color="blue"
          >
            {busy ? "Processing..." : "Submit Record"}
          </Button>
        </FormSection>
      </Card>

      <Alert variant="light" color="gray" icon={<FaHistory />} mt="md">
        <Text size="sm">
          All actions are logged in the RequestAction history table. No workflow
          tasks are created for offline-sanctioned records or maintenance actions.
        </Text>
      </Alert>
    </Container>
  );
}
