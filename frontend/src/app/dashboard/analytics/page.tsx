"use client";
// frontend/src/app/dashboard/analytics/page.tsx

import { useEffect, useState } from "react";
import { reviewsApi, businessApi } from "@/lib/api";
import { Analytics, Business } from "@/types";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend
} from "recharts";
import { Star, TrendingUp, Clock, CheckCircle2, BarChart3 } from "lucide-react";

const RATING_COLORS = ["#ef4444", "#f97316", "#eab308", "#84cc16", "#22c55e"];

export default function AnalyticsPage() {
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [businesses, setBusinesses] = useState<Business[]>([]);
  const [selectedBiz, setSelectedBiz] = useState<string>("");
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const [analyticsRes, bizRes] = await Promise.all([
        reviewsApi.analytics(selectedBiz || undefined),
        businessApi.list(),
      ]);
      setAnalytics(analyticsRes.data);
      setBusinesses(bizRes.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [selectedBiz]);

  // Prepare chart data
  const ratingBarData = analytics
    ? [5, 4, 3, 2, 1].map((r) => ({
        rating: `${r}★`,
        count: analytics.rating_distribution[String(r)] || 0,
        fill: RATING_COLORS[r - 1],
      }))
    : [];

  const replyPieData = analytics
    ? [
        { name: "Pending", value: analytics.pending_replies, color: "#f59e0b" },
        { name: "Approved", value: analytics.approved_replies, color: "#22c55e" },
      ].filter((d) => d.value > 0)
    : [];

  const statCards = analytics
    ? [
        {
          label: "Total Reviews",
          value: analytics.total_reviews,
          icon: Star,
          color: "text-amber-500 bg-amber-50",
        },
        {
          label: "Avg Rating",
          value: analytics.avg_rating ? `${analytics.avg_rating.toFixed(1)} / 5` : "—",
          icon: TrendingUp,
          color: "text-brand-500 bg-brand-50",
        },
        {
          label: "This Week",
          value: analytics.reviews_this_week,
          icon: BarChart3,
          color: "text-violet-500 bg-violet-50",
        },
        {
          label: "Pending",
          value: analytics.pending_replies,
          icon: Clock,
          color: "text-orange-500 bg-orange-50",
        },
        {
          label: "Approved",
          value: analytics.approved_replies,
          icon: CheckCircle2,
          color: "text-emerald-500 bg-emerald-50",
        },
      ]
    : [];

  return (
    <div className="space-y-6 max-w-5xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-3xl font-bold text-zinc-900">Analytics</h1>
          <p className="text-zinc-500 mt-1">Review performance and reply statistics</p>
        </div>
        <select
          className="input py-2 w-auto text-sm"
          value={selectedBiz}
          onChange={(e) => setSelectedBiz(e.target.value)}
        >
          <option value="">All Businesses</option>
          {businesses.map((b) => (
            <option key={b.id} value={b.id}>{b.business_name}</option>
          ))}
        </select>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-48">
          <div className="w-8 h-8 border-[3px] border-brand-500 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : !analytics ? null : (
        <>
          {/* Stat Cards */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            {statCards.map(({ label, value, icon: Icon, color }) => (
              <div key={label} className="card p-4 text-center">
                <div className={`w-9 h-9 rounded-xl ${color} flex items-center justify-center mx-auto mb-2`}>
                  <Icon className="w-4 h-4" />
                </div>
                <p className="font-display font-bold text-zinc-900 text-xl">{value}</p>
                <p className="text-xs text-zinc-500 mt-0.5">{label}</p>
              </div>
            ))}
          </div>

          {/* Charts Row */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {/* Rating Distribution Bar Chart */}
            <div className="card p-5">
              <h3 className="font-display font-semibold text-zinc-900 mb-4">Rating Distribution</h3>
              {analytics.total_reviews === 0 ? (
                <div className="h-48 flex items-center justify-center text-zinc-400 text-sm">
                  No data yet
                </div>
              ) : (
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={ratingBarData} barSize={32}>
                    <XAxis dataKey="rating" axisLine={false} tickLine={false} tick={{ fontSize: 13 }} />
                    <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 12 }} allowDecimals={false} />
                    <Tooltip
                      cursor={{ fill: "#f4f4f5" }}
                      contentStyle={{ borderRadius: 12, border: "1px solid #e4e4e7", fontSize: 13 }}
                    />
                    <Bar dataKey="count" name="Reviews" radius={[6, 6, 0, 0]}>
                      {ratingBarData.map((entry, i) => (
                        <Cell key={i} fill={entry.fill} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>

            {/* Reply Status Pie Chart */}
            <div className="card p-5">
              <h3 className="font-display font-semibold text-zinc-900 mb-4">Reply Status</h3>
              {replyPieData.length === 0 ? (
                <div className="h-48 flex items-center justify-center text-zinc-400 text-sm">
                  No replies generated yet
                </div>
              ) : (
                <ResponsiveContainer width="100%" height={200}>
                  <PieChart>
                    <Pie
                      data={replyPieData}
                      cx="50%"
                      cy="50%"
                      innerRadius={55}
                      outerRadius={80}
                      paddingAngle={4}
                      dataKey="value"
                    >
                      {replyPieData.map((entry, i) => (
                        <Cell key={i} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip contentStyle={{ borderRadius: 12, border: "1px solid #e4e4e7", fontSize: 13 }} />
                    <Legend
                      iconType="circle"
                      iconSize={10}
                      wrapperStyle={{ fontSize: 13 }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
