import { lazy } from "react";
import { Navigate, type RouteObject } from "react-router-dom";

const ApplyLeavePage = lazy(() => import("./pages/ApplyLeavePage"));
const BalancesPage = lazy(() => import("./pages/BalancesPage"));
const MyRequestsPage = lazy(() => import("./pages/MyRequestsPage"));
const PolicyAdminPage = lazy(() => import("./pages/PolicyAdminPage"));
const CalendarAdminPage = lazy(() => import("./pages/CalendarAdminPage"));
const RecordsAdminPage = lazy(() => import("./pages/RecordsAdminPage"));
const RequestDetailPage = lazy(() => import("./pages/RequestDetailPage"));
const ReviewQueuePage = lazy(() => import("./pages/ReviewQueuePage"));

export const routes: RouteObject[] = [
  { index: true, element: <Navigate to="mine" replace /> },
  { path: "mine", element: <MyRequestsPage /> },
  { path: "balances", element: <BalancesPage /> },
  { path: "history", element: <MyRequestsPage /> },
  { path: "create", element: <ApplyLeavePage /> },
  { path: "tasks", element: <ReviewQueuePage /> },
  { path: "request/:id", element: <RequestDetailPage /> },
  { path: "admin/policy", element: <PolicyAdminPage /> },
  { path: "admin/calendar", element: <CalendarAdminPage /> },
  { path: "admin/records", element: <RecordsAdminPage /> },
];
