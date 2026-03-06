// frontend/src/components/ui/StatusBadge.tsx

import clsx from "clsx";
import { Clock, CheckCircle, XCircle } from "lucide-react";

interface Props {
  status: "pending" | "approved" | "rejected";
}

const config = {
  pending: {
    icon: Clock,
    label: "Pending",
    className: "bg-amber-50 text-amber-700 border border-amber-100",
  },
  approved: {
    icon: CheckCircle,
    label: "Approved",
    className: "bg-brand-50 text-brand-700 border border-brand-100",
  },
  rejected: {
    icon: XCircle,
    label: "Rejected",
    className: "bg-red-50 text-red-700 border border-red-100",
  },
};

export default function StatusBadge({ status }: Props) {
  const { icon: Icon, label, className } = config[status];
  return (
    <span className={clsx("badge", className)}>
      <Icon className="w-3 h-3" />
      {label}
    </span>
  );
}
