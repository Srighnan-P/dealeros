"use client";

import { useEffect, useState } from "react";

interface Disagreement {
  reason: string;
  record_id: string | null;
  entry_id: string | null;
  location: string | null;
  a_value: string | null;
  b_value: string | null;
  difference: string | null;
}

interface DisagreementResponse {
  disagreements: Disagreement[];
}

const reasons = [
  "MISSING_IN_B",
  "ORPHAN_IN_B",
  "DUPLICATE_IN_B",
  "VALUE_MISMATCH",
  "LOCATION_MISMATCH",
  "DATE_MISMATCH",
];

export default function Home() {
  const [organization, setOrganization] = useState("ORG-A");
  const [reason, setReason] = useState("");
  const [sort, setSort] = useState("value");
  const [disagreements, setDisagreements] = useState<Disagreement[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const controller = new AbortController();

    async function fetchDisagreements() {
      setLoading(true);
      setError("");

      const params = new URLSearchParams();
      params.set("org", organization);
      if (reason) {
        params.set("reason", reason);
      }
      params.set("sort", sort);

      const apiUrl = "https://backend-drab-alpha-20.vercel.app";

      try {
        const response = await fetch(
          `${apiUrl}/api/disagreements/?${params.toString()}`,
          { signal: controller.signal }
        );

        if (!response.ok) {
          throw new Error(`API request failed with status ${response.status}`);
        }

        const data: Disagreement[] | DisagreementResponse =
          await response.json();
        const results = Array.isArray(data) ? data : data.disagreements;
        setDisagreements(results);
      } catch (requestError) {
        if (requestError instanceof Error && requestError.name === "AbortError") {
          return;
        }

        setError(
          requestError instanceof Error
            ? requestError.message
            : "Unable to load disagreements."
        );
        setDisagreements([]);
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    fetchDisagreements();

    return () => {
      controller.abort();
    };
  }, [organization, reason, sort]);

  function displayMoney(value: string | null) {
    return value === null || value === undefined ? "—" : value;
  }

  return (
    <main className="mx-auto min-h-screen max-w-7xl bg-white px-4 py-8 sm:px-6 lg:px-8">
      <header className="mb-6">
        <h1 className="text-2xl font-semibold text-slate-900">
          DealerOS — Reconciliation Dashboard
        </h1>
      </header>

      <section
        aria-label="Dashboard filters"
        className="mb-6 rounded-lg border border-slate-200 bg-white p-4 shadow-sm"
      >
        <div className="grid gap-4 sm:grid-cols-3">
          <div>
            <label
              htmlFor="organization"
              className="mb-1 block text-sm font-medium text-slate-700"
            >
              Organization
            </label>
            <select
              id="organization"
              value={organization}
              onChange={(event) => setOrganization(event.target.value)}
              className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-slate-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
            >
              <option value="ORG-A">ORG-A</option>
              <option value="ORG-B">ORG-B</option>
            </select>
          </div>

          <div>
            <label
              htmlFor="reason"
              className="mb-1 block text-sm font-medium text-slate-700"
            >
              Reason
            </label>
            <select
              id="reason"
              value={reason}
              onChange={(event) => setReason(event.target.value)}
              className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-slate-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
            >
              <option value="">All reasons</option>
              {reasons.map((reasonOption) => (
                <option key={reasonOption} value={reasonOption}>
                  {reasonOption}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label
              htmlFor="sort"
              className="mb-1 block text-sm font-medium text-slate-700"
            >
              Value sort
            </label>
            <select
              id="sort"
              value={sort}
              onChange={(event) => setSort(event.target.value)}
              className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-slate-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
            >
              <option value="value">Ascending</option>
              <option value="-value">Descending</option>
            </select>
          </div>
        </div>
      </section>

      {loading && (
        <p className="rounded-md border border-slate-200 bg-white px-4 py-6 text-center text-slate-600">
          Loading...
        </p>
      )}

      {!loading && error && (
        <p className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-red-700">
          Error: {error}
        </p>
      )}

      {!loading && !error && disagreements.length === 0 && (
        <p className="rounded-md border border-slate-200 bg-white px-4 py-6 text-center text-slate-600">
          No disagreements found
        </p>
      )}

      {!loading && !error && disagreements.length > 0 && (
        <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white shadow-sm">
          <table className="min-w-full border-collapse text-left text-sm">
            <thead className="border-b border-slate-200 bg-slate-50">
              <tr>
                <th className="px-4 py-3 font-semibold text-slate-700">Reason</th>
                <th className="px-4 py-3 font-semibold text-slate-700">
                  Record ID
                </th>
                <th className="px-4 py-3 font-semibold text-slate-700">
                  Location
                </th>
                <th className="px-4 py-3 font-semibold text-slate-700">
                  System A Value
                </th>
                <th className="px-4 py-3 font-semibold text-slate-700">
                  System B Value
                </th>
                <th className="px-4 py-3 font-semibold text-slate-700">
                  Difference
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {disagreements.map((disagreement, index) => (
                <tr
                  key={`${disagreement.reason}-${disagreement.record_id ?? disagreement.entry_id ?? index}`}
                  className="hover:bg-slate-50"
                >
                  <td className="px-4 py-3 font-medium text-slate-900">
                    {disagreement.reason}
                  </td>
                  <td className="px-4 py-3 text-slate-700">
                    {disagreement.record_id ?? "—"}
                  </td>
                  <td className="px-4 py-3 text-slate-700">
                    {disagreement.location ?? "—"}
                  </td>
                  <td className="px-4 py-3 text-right tabular-nums text-slate-700">
                    {displayMoney(disagreement.a_value)}
                  </td>
                  <td className="px-4 py-3 text-right tabular-nums text-slate-700">
                    {displayMoney(disagreement.b_value)}
                  </td>
                  <td className="px-4 py-3 text-right tabular-nums text-slate-700">
                    {displayMoney(disagreement.difference)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </main>
  );
}
