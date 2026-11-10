import { lazy } from "react";
import { Navigate, type RouteObject } from "react-router-dom";

/** One lazy chunk per page. Vite can only split these if the import() argument
 *  is a static literal — a computed path silently bundles everything. */
const LeaveApplicationsPage = lazy(() => import("./pages/LeaveApplicationsPage"));
const MyLeaveBalancePage = lazy(() => import("./pages/MyLeaveBalancePage"));
const LeaveHistoryPage = lazy(() => import("./pages/LeaveHistoryPage"));
const PolicyConfigurationPage = lazy(() => import("./pages/PolicyConfigurationPage"));
const HolidayCalendarPage = lazy(() => import("./pages/HolidayCalendarPage"));
const SLAConfigurationPage = lazy(() => import("./pages/SLAConfigurationPage"));
const OfflineSanctionRecordPage = lazy(() => import("./pages/OfflineSanctionRecordPage"));
const ResumptionReviewPage = lazy(() => import("./pages/ResumptionReviewPage"));

/** Paths are RELATIVE — the shell mounts them under the manifest's basePath.
 *
 *  Every entry here has a matching nav item in the server's registry.py, and
 *  that correspondence matters: the sidebar is built server-side, so a nav item
 *  without a route here renders a link that goes nowhere. */
export const routes: RouteObject[] = [
  { index: true, element: <Navigate to="leave-applications" replace /> },
  { path: "leave-applications", element: <LeaveApplicationsPage /> },
  { path: "my-leave-balance", element: <MyLeaveBalancePage /> },
  { path: "leave-history", element: <LeaveHistoryPage /> },
  { path: "policy-configuration", element: <PolicyConfigurationPage /> },
  { path: "holiday-calendar", element: <HolidayCalendarPage /> },
  { path: "sla-configuration", element: <SLAConfigurationPage /> },
  { path: "offline-sanction-record", element: <OfflineSanctionRecordPage /> },
  { path: "resumption-review", element: <ResumptionReviewPage /> },
];
