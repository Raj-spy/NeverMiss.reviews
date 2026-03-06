"use client";
// frontend/src/app/dashboard/page.tsx
// Main dashboard: stats cards + recent reviews

import { useEffect, useState } from "react";
import Link from "next/link";
import { reviewsApi, businessApi } from "@/lib/api";
import { Analytics, Review, Business } from "@/types";
import StarRating from "@/components/ui/StarRating";
import StatusBadge from "@/components/ui/StatusBadge";
import {
  Star, Building2, Clock, CheckCircle2,
  TrendingUp, ArrowRight, RefreshCw
} from "lucide-react";
import { formatDistanceToNow } from "date-fns";

export default function DashboardPage() {
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [recentReviews, setRecentReviews] = useState<Review[]>([]);
  const [businesses, setBusinesses] = useState<Business[]>([]);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    try {
      const [analyticsRes, reviewsRes, bizRes] = await Promise.all([
        reviewsApi.analytics(),
        reviewsApi.list({ limit: 5 }),
        businessApi.list(),
      ]);
      setAnalytics(analyticsRes.data);
      setRecentReviews(reviewsRes.data);
      setBusinesses(bizRes.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-3 border-brand-500 border-t-transparent rounded-full animate-spin border-[3px]" />
      </div>
    );
  }

  const stats = [
    {
      label: "Total Reviews",
      value: analytics?.total_reviews ?? 0,
      icon: Star,
      color: "bg-amber-50 text-amber-600",
      trend: `+${analytics?.reviews_this_week ?? 0} this week`,
    },
    {
      label: "Avg Rating",
      value: analytics?.avg_rating ? analytics.avg_rating.toFixed(1) : "—",
      icon: TrendingUp,
      color: "bg-brand-50 text-brand-600",
      trend: "across all businesses",
    },
    {
      label: "Pending Replies",
      value: analytics?.pending_replies ?? 0,
      icon: Clock,
      color: "bg-orange-50 text-orange-600",
      trend: "need your attention",
    },
    {
      label: "Approved Replies",
      value: analytics?.approved_replies ?? 0,
      icon: CheckCircle2,
      color: "bg-emerald-50 text-emerald-600",
      trend: "published responses",
    },
  ];

  return (
    <div className="space-y-8 max-w-6xl">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-3xl font-bold text-zinc-900">Dashboard</h1>
          <p className="text-zinc-500 mt-1">Your review performance at a glance</p>
        </div>
        <button
          onClick={load}
          className="btn-secondary flex items-center gap-2 text-sm"
        >
          <RefreshCw className="w-4 h-4" /> Refresh
        </button>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map(({ label, value, icon: Icon, color, trend }) => (
          <div key={label} className="card p-5">
            <div className={`w-10 h-10 rounded-xl flex items-center justify-center mb-3 ${color}`}>
              <Icon className="w-5 h-5" />
            </div>
            <p className="text-2xl font-display font-bold text-zinc-900">{value}</p>
            <p className="text-sm font-medium text-zinc-700 mt-0.5">{label}</p>
            <p className="text-xs text-zinc-400 mt-1">{trend}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Reviews */}
        <div className="lg:col-span-2 card">
          <div className="flex items-center justify-between px-6 py-4 border-b border-zinc-100">
            <h2 className="font-display font-semibold text-zinc-900">Recent Reviews</h2>
            <Link href="/dashboard/reviews" className="text-sm text-brand-600 hover:text-brand-700 flex items-center gap-1">
              View all <ArrowRight className="w-3 h-3" />
            </Link>
          </div>
          <div className="divide-y divide-zinc-50">
            {recentReviews.length === 0 ? (
              <div className="px-6 py-10 text-center text-zinc-400 text-sm">
                No reviews yet. Add a business to get started.
              </div>
            ) : (
              recentReviews.map((review) => (
                <div key={review.id} className="px-6 py-4 hover:bg-surface-50 transition-colors">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1.5">
                        <StarRating rating={review.rating} size="sm" />
                        {review.reply && <StatusBadge status={review.reply.status} />}
                      </div>
                      <p className="text-sm text-zinc-700 line-clamp-2">{review.review_text}</p>
                      <div className="flex items-center gap-2 mt-2">
                        <span className="text-xs text-zinc-400">
                          {review.reviewer_name || "Anonymous"}
                        </span>
                        <span className="text-zinc-200">·</span>
                        <span className="text-xs text-zinc-400">{review.business_name}</span>
                        <span className="text-zinc-200">·</span>
                        <span className="text-xs text-zinc-400">
                          {formatDistanceToNow(new Date(review.created_at), { addSuffix: true })}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Businesses */}
        <div className="card">
          <div className="flex items-center justify-between px-6 py-4 border-b border-zinc-100">
            <h2 className="font-display font-semibold text-zinc-900">Businesses</h2>
            <Link href="/dashboard/business" className="text-sm text-brand-600 hover:text-brand-700 flex items-center gap-1">
              Manage <ArrowRight className="w-3 h-3" />
            </Link>
          </div>
          <div className="divide-y divide-zinc-50">
            {businesses.length === 0 ? (
              <div className="px-6 py-10 text-center">
                <Building2 className="w-8 h-8 text-zinc-300 mx-auto mb-2" />
                <p className="text-zinc-400 text-sm">No businesses added yet</p>
                <Link href="/dashboard/business" className="text-brand-600 text-sm font-medium mt-2 inline-block">
                  Add your first business →
                </Link>
              </div>
            ) : (
              businesses.map((biz) => (
                <div key={biz.id} className="px-6 py-4 hover:bg-surface-50 transition-colors">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-zinc-900">{biz.business_name}</p>
                      <p className="text-xs text-zinc-400 mt-0.5">{biz.review_count} reviews</p>
                    </div>
                    {biz.avg_rating && (
                      <div className="flex items-center gap-1">
                        <Star className="w-3.5 h-3.5 fill-amber-400 text-amber-400" />
                        <span className="text-sm font-medium text-zinc-700">{biz.avg_rating}</span>
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
