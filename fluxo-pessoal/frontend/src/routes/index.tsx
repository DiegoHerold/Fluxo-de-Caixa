import { Navigate, Route, Routes } from "react-router-dom";
import { AppLayout } from "../components/layout/AppLayout";
import { AccountsPage } from "../pages/AccountsPage";
import { BalancesPage } from "../pages/BalancesPage";
import { ChartAccountsPage } from "../pages/ChartAccountsPage";
import { ClassificationRulesPage } from "../pages/ClassificationRulesPage";
import { DashboardPage } from "../pages/DashboardPage";
import { ImportPage } from "../pages/ImportPage";
import { PendingTransactionsPage } from "../pages/PendingTransactionsPage";
import { ReportIndicatorsPage } from "../pages/ReportIndicatorsPage";
import { ReportsPage } from "../pages/ReportsPage";
import { TransactionsPage } from "../pages/TransactionsPage";

export function AppRoutes() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route index element={<DashboardPage />} />
        <Route path="accounts" element={<AccountsPage />} />
        <Route path="imports" element={<ImportPage />} />
        <Route path="transactions" element={<TransactionsPage />} />
        <Route path="pending" element={<PendingTransactionsPage />} />
        <Route path="chart-accounts" element={<ChartAccountsPage />} />
        <Route path="indicators" element={<ReportIndicatorsPage />} />
        <Route path="rules" element={<ClassificationRulesPage />} />
        <Route path="reports" element={<ReportsPage />} />
        <Route path="balances" element={<BalancesPage />} />
        <Route path="dashboard" element={<Navigate to="/" replace />} />
        <Route path="import" element={<Navigate to="/imports" replace />} />
        <Route path="pending-transactions" element={<Navigate to="/pending" replace />} />
        <Route path="classification-rules" element={<Navigate to="/rules" replace />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
