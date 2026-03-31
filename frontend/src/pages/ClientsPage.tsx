import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  useReactTable,
} from "@tanstack/react-table";
import { toast } from "sonner";

import api from "@/lib/api";
import type {
  Client,
  ClientCreatePayload,
  ClientStatus,
  ClientTier,
} from "@/types";

/* ═══════════════════════════════════════════════════════════════════════════════
   Badge helpers
   ═══════════════════════════════════════════════════════════════════════════ */

const STATUS_COLORS: Record<ClientStatus, string> = {
  DRAFT: "bg-slate-100 text-slate-700",
  KYC_PENDING: "bg-yellow-100 text-yellow-800",
  AGREEMENT_SENT: "bg-blue-100 text-blue-800",
  SIGNED: "bg-purple-100 text-purple-800",
  ACTIVE: "bg-green-100 text-green-800",
};

const TIER_COLORS: Record<ClientTier, string> = {
  ESSENTIAL: "bg-slate-100 text-slate-700",
  GROWTH: "bg-blue-100 text-blue-800",
  PREMIUM: "bg-purple-100 text-purple-800",
  ELITE: "bg-amber-100 text-amber-800",
};

function Badge({ label, colorClass }: { label: string; colorClass: string }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${colorClass}`}
    >
      {label}
    </span>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════════
   Table columns
   ═══════════════════════════════════════════════════════════════════════════ */

const col = createColumnHelper<Client>();

const columns = [
  col.accessor("full_name", {
    header: "Name",
    cell: (info) => (
      <span className="font-medium text-gray-900">{info.getValue()}</span>
    ),
  }),
  col.accessor("email", { header: "Email" }),
  col.accessor("status", {
    header: "Status",
    cell: (info) => {
      const v = info.getValue();
      return <Badge label={v} colorClass={STATUS_COLORS[v]} />;
    },
  }),
  col.accessor("tier", {
    header: "Tier",
    cell: (info) => {
      const v = info.getValue();
      return v ? <Badge label={v} colorClass={TIER_COLORS[v]} /> : "—";
    },
  }),
  col.accessor("created_at", {
    header: "Created",
    cell: (info) => new Date(info.getValue()).toLocaleDateString(),
  }),
  col.display({
    id: "actions",
    header: "",
    cell: (info) => (
      <a
        href={`/clients/${info.row.original.id}`}
        className="text-sm font-medium text-blue-600 hover:underline"
      >
        View
      </a>
    ),
  }),
];

/* ═══════════════════════════════════════════════════════════════════════════════
   New Client Form
   ═══════════════════════════════════════════════════════════════════════════ */

const EMPLOYMENT_OPTIONS = [
  "Employed",
  "Self-Employed",
  "Retired",
  "Student",
  "Unemployed",
];

const TAX_FILING_OPTIONS = [
  "Single",
  "Married Filing Jointly",
  "Married Filing Separately",
  "Head of Household",
];

const INITIAL_FORM: ClientCreatePayload = {
  first_name: "",
  last_name: "",
  email: "",
  phone: "",
  date_of_birth: "",
  ssn: "",
  employment_status: "",
  annual_income: undefined,
  tax_filing_status: "",
  ai_consent: false,
};

function NewClientDialog({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const queryClient = useQueryClient();
  const [form, setForm] = useState<ClientCreatePayload>({ ...INITIAL_FORM });

  const mutation = useMutation({
    mutationFn: (payload: ClientCreatePayload) =>
      api.post<Client>("/clients", payload).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["clients"] });
      toast.success("Client created successfully");
      setForm({ ...INITIAL_FORM });
      onClose();
    },
    onError: () => {
      toast.error("Failed to create client");
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const payload: ClientCreatePayload = {
      ...form,
      annual_income: form.annual_income ? Number(form.annual_income) : undefined,
    };
    mutation.mutate(payload);
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
      <div className="w-full max-w-lg rounded-xl bg-white p-6 shadow-xl max-h-[90vh] overflow-y-auto">
        <h2 className="mb-4 text-lg font-semibold text-gray-900">
          New Client
        </h2>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Name row */}
          <div className="grid grid-cols-2 gap-3">
            <Field
              label="First name"
              value={form.first_name}
              onChange={(v) => setForm({ ...form, first_name: v })}
              required
            />
            <Field
              label="Last name"
              value={form.last_name}
              onChange={(v) => setForm({ ...form, last_name: v })}
              required
            />
          </div>

          <Field
            label="Email"
            type="email"
            value={form.email}
            onChange={(v) => setForm({ ...form, email: v })}
            required
          />

          <div className="grid grid-cols-2 gap-3">
            <Field
              label="Phone"
              type="tel"
              value={form.phone ?? ""}
              onChange={(v) => setForm({ ...form, phone: v })}
            />
            <Field
              label="Date of birth"
              type="date"
              value={form.date_of_birth ?? ""}
              onChange={(v) => setForm({ ...form, date_of_birth: v })}
            />
          </div>

          <Field
            label="SSN"
            type="password"
            value={form.ssn ?? ""}
            onChange={(v) => setForm({ ...form, ssn: v })}
            placeholder="•••-••-••••"
            autoComplete="off"
          />

          <Select
            label="Employment status"
            value={form.employment_status ?? ""}
            onChange={(v) => setForm({ ...form, employment_status: v })}
            options={EMPLOYMENT_OPTIONS}
          />

          <Field
            label="Annual income"
            type="number"
            value={form.annual_income?.toString() ?? ""}
            onChange={(v) =>
              setForm({ ...form, annual_income: v ? Number(v) : undefined })
            }
          />

          <Select
            label="Tax filing status"
            value={form.tax_filing_status ?? ""}
            onChange={(v) => setForm({ ...form, tax_filing_status: v })}
            options={TAX_FILING_OPTIONS}
          />

          {/* AI Consent */}
          <label className="flex items-start gap-3 rounded-lg border border-gray-200 p-3">
            <input
              type="checkbox"
              checked={form.ai_consent}
              onChange={(e) =>
                setForm({ ...form, ai_consent: e.target.checked })
              }
              className="mt-0.5 h-4 w-4 accent-blue-600"
            />
            <span className="text-sm text-gray-600">
              I consent to AI-assisted portfolio analysis and recommendations in
              accordance with the platform disclosure.
            </span>
          </label>

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={mutation.isPending}
              className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {mutation.isPending ? "Creating…" : "Create Client"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

/* ── Reusable form primitives ──────────────────────────────────────────────── */

function Field({
  label,
  value,
  onChange,
  type = "text",
  required = false,
  placeholder,
  autoComplete,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  type?: string;
  required?: boolean;
  placeholder?: string;
  autoComplete?: string;
}) {
  return (
    <label className="block">
      <span className="mb-1 block text-sm font-medium text-gray-700">
        {label}
      </span>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        required={required}
        placeholder={placeholder}
        autoComplete={autoComplete}
        className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
      />
    </label>
  );
}

function Select({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: string[];
}) {
  return (
    <label className="block">
      <span className="mb-1 block text-sm font-medium text-gray-700">
        {label}
      </span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
      >
        <option value="">Select…</option>
        {options.map((opt) => (
          <option key={opt} value={opt}>
            {opt}
          </option>
        ))}
      </select>
    </label>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════════
   Skeleton / empty / error states
   ═══════════════════════════════════════════════════════════════════════════ */

function TableSkeleton() {
  return (
    <div className="space-y-3">
      {Array.from({ length: 5 }).map((_, i) => (
        <div
          key={i}
          className="h-12 animate-pulse rounded-lg bg-gray-100"
        />
      ))}
    </div>
  );
}

function EmptyState({ onAdd }: { onAdd: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center rounded-xl border-2 border-dashed border-gray-200 py-16 text-center">
      <svg
        className="mb-4 h-12 w-12 text-gray-300"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1.5}
          d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z"
        />
      </svg>
      <h3 className="mb-1 text-sm font-semibold text-gray-900">
        No clients yet
      </h3>
      <p className="mb-4 text-sm text-gray-500">
        Get started by adding your first client.
      </p>
      <button
        onClick={onAdd}
        className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
      >
        New Client
      </button>
    </div>
  );
}

function ErrorBanner({ message }: { message: string }) {
  return (
    <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
      {message}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════════
   Page component
   ═══════════════════════════════════════════════════════════════════════════ */

export default function ClientsPage() {
  const [dialogOpen, setDialogOpen] = useState(false);

  const {
    data: clients,
    isLoading,
    isError,
    error,
  } = useQuery<Client[]>({
    queryKey: ["clients"],
    queryFn: () => api.get<Client[]>("/clients").then((r) => r.data),
  });

  const table = useReactTable({
    data: clients ?? [],
    columns,
    getCoreRowModel: getCoreRowModel(),
  });

  return (
    <div className="mx-auto max-w-6xl px-4 py-8">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Clients</h1>
          <p className="text-sm text-gray-500">
            Manage your client onboarding pipeline
          </p>
        </div>
        <button
          onClick={() => setDialogOpen(true)}
          className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-blue-700"
        >
          + New Client
        </button>
      </div>

      {/* Content */}
      {isLoading && <TableSkeleton />}

      {isError && (
        <ErrorBanner
          message={
            error instanceof Error ? error.message : "Failed to load clients"
          }
        />
      )}

      {!isLoading && !isError && clients?.length === 0 && (
        <EmptyState onAdd={() => setDialogOpen(true)} />
      )}

      {!isLoading && !isError && clients && clients.length > 0 && (
        <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              {table.getHeaderGroups().map((hg) => (
                <tr key={hg.id}>
                  {hg.headers.map((header) => (
                    <th
                      key={header.id}
                      className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500"
                    >
                      {header.isPlaceholder
                        ? null
                        : flexRender(
                            header.column.columnDef.header,
                            header.getContext(),
                          )}
                    </th>
                  ))}
                </tr>
              ))}
            </thead>
            <tbody className="divide-y divide-gray-100">
              {table.getRowModel().rows.map((row) => (
                <tr key={row.id} className="hover:bg-gray-50">
                  {row.getVisibleCells().map((cell) => (
                    <td
                      key={cell.id}
                      className="whitespace-nowrap px-4 py-3 text-sm text-gray-600"
                    >
                      {flexRender(
                        cell.column.columnDef.cell,
                        cell.getContext(),
                      )}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Dialog */}
      <NewClientDialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
      />
    </div>
  );
}
