// frontend/src/components/ui/StarRating.tsx

import { Star } from "lucide-react";
import clsx from "clsx";

interface Props {
  rating: number;
  size?: "sm" | "md" | "lg";
  showNumber?: boolean;
}

export default function StarRating({ rating, size = "md", showNumber = false }: Props) {
  const sizes = { sm: "w-3 h-3", md: "w-4 h-4", lg: "w-5 h-5" };
  const sz = sizes[size];

  return (
    <div className="flex items-center gap-1">
      <div className="flex items-center gap-0.5">
        {[1, 2, 3, 4, 5].map((i) => (
          <Star
            key={i}
            className={clsx(sz, i <= rating ? "fill-amber-400 text-amber-400" : "fill-zinc-100 text-zinc-200")}
          />
        ))}
      </div>
      {showNumber && (
        <span className="text-sm font-medium text-zinc-600 ml-1">{rating.toFixed(1)}</span>
      )}
    </div>
  );
}
