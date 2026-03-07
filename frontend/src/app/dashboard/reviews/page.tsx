"use client";
// frontend/src/app/dashboard/reviews/page.tsx

import { useEffect, useState, useCallback } from "react";
import { reviewsApi, repliesApi, businessApi } from "@/lib/api";
import { Review, Business } from "@/types";
import StarRating from "@/components/ui/StarRating";
import StatusBadge from "@/components/ui/StatusBadge";
import {
  Check, X, Copy, RefreshCw, ChevronDown,
  MessageSquare, Edit3, Sparkles, Filter
} from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import clsx from "clsx";

export default function ReviewsPage() {
  const [reviews, setReviews] = useState<Review[]>([]);
  const [businesses, setBusinesses] = useState<Business[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedBiz, setSelectedBiz] = useState<string>("");
  const [selectedRating, setSelectedRating] = useState<string>("");
  const [editingReply, setEditingReply] = useState<{ [reviewId: string]: string }>({});
  const [editMode, setEditMode] = useState<{ [reviewId: string]: boolean }>({});
  const [actionLoading, setActionLoading] = useState<{ [id: string]: boolean }>({});
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [expandedReview, setExpandedReview] = useState<string | null>(null);

  // ── Fix 1: useCallback so load() is stable and can be called after actions ──
  const load = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, string | number | boolean> = {};
      if (selectedBiz) params.business_id = selectedBiz;
      if (selectedRating) params.rating = parseInt(selectedRating);

      const [reviewsRes, bizRes] = await Promise.all([
        reviewsApi.list(params),
        businessApi.list(),
      ]);
      setReviews(reviewsRes.data);
      setBusinesses(bizRes.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [selectedBiz, selectedRating]);

  useEffect(() => { load(); }, [load]);

  // ── Fix 2: Use functional state updates to avoid stale closure on actionLoading ──
  const setItemLoading = (id: string, value: boolean) =>
    setActionLoading((prev) => ({ ...prev, [id]: value }));

  const handleApprove = async (reviewId: string, replyId: string) => {
    setItemLoading(replyId, true);
    try {
      const editedText = editingReply[reviewId];
      await repliesApi.approve(replyId, editedText);
      // Fix 3: Update local state immediately so UI reflects change without waiting for reload
      setReviews((prev) =>
        prev.map((r) =>
          r.id === reviewId && r.reply
            ? {
                ...r,
                reply: {
                  ...r.reply,
                  status: "approved",
                  reply_text: editedText ?? r.reply.reply_text,
                },
              }
            : r
        )
      );
      setEditMode((prev) => ({ ...prev, [reviewId]: false }));
    } catch (err) {
      alert("Failed to approve reply");
    } finally {
      setItemLoading(replyId, false);
    }
  };

  const handleReject = async (reviewId: string, replyId: string) => {
    setItemLoading(replyId, true);
    try {
      await repliesApi.reject(replyId);
      // Update local state immediately
      setReviews((prev) =>
        prev.map((r) =>
          r.id === reviewId && r.reply
            ? { ...r, reply: { ...r.reply, status: "rejected" } }
            : r
        )
      );
    } catch (err) {
      alert("Failed to reject reply");
    } finally {
      setItemLoading(replyId, false);
    }
  };

  const handleRegenerate = async (reviewId: string) => {
    setItemLoading(reviewId, true);
    try {
      const res = await repliesApi.regenerate(reviewId);
      // Fix 4: Use the response data directly to update the reply in state
      const newReply = res.data;
      setReviews((prev) =>
        prev.map((r) =>
          r.id === reviewId ? { ...r, reply: newReply } : r
        )
      );
    } catch (err) {
      alert("Failed to regenerate reply");
    } finally {
      setItemLoading(reviewId, false);
    }
  };

  const handleCopy = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const toggleEdit = (reviewId: string, currentText: string) => {
    setEditMode((prev) => ({ ...prev, [reviewId]: !prev[reviewId] }));
    setEditingReply((prev) => ({ ...prev, [reviewId]: prev[reviewId] ?? currentText }));
  };

  const ratingColor = (r: number) =>
    r >= 4 ? "border-l-brand-400" : r === 3 ? "border-l-amber-400" : "border-l-red-400";

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Header */}
      <div>
        <h1 className="font-display text-3xl font-bold text-zinc-900">Reviews</h1>
        <p className="text-zinc-500 mt-1">Manage AI reply suggestions for your Google reviews</p>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3 flex-wrap">
        <div className="flex items-center gap-2 text-sm text-zinc-500">
          <Filter className="w-4 h-4" /> Filter:
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

        <select
          className="input py-2 w-auto text-sm"
          value={selectedRating}
          onChange={(e) => setSelectedRating(e.target.value)}
        >
          <option value="">All Ratings</option>
          {[5, 4, 3, 2, 1].map((r) => (
            <option key={r} value={r}>{r} Stars</option>
          ))}
        </select>

        <button onClick={load} className="btn-ghost flex items-center gap-1.5 text-sm py-2">
          <RefreshCw className="w-3.5 h-3.5" /> Refresh
        </button>

        <span className="text-sm text-zinc-400 ml-auto">{reviews.length} reviews</span>
      </div>

      {/* Review List */}
      {loading ? (
        <div className="flex items-center justify-center h-48">
          <div className="w-8 h-8 border-[3px] border-brand-500 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : reviews.length === 0 ? (
        <div className="card p-16 text-center">
          <MessageSquare className="w-10 h-10 text-zinc-300 mx-auto mb-3" />
          <p className="text-zinc-500 text-sm">No reviews found</p>
        </div>
      ) : (
        <div className="space-y-3">
          {reviews.map((review) => (
            <div
              key={review.id}
              className={clsx(
                "card border-l-4 overflow-hidden transition-all duration-200",
                ratingColor(review.rating)
              )}
            >
              {/* Review Header */}
              <div
                className="px-5 py-4 cursor-pointer hover:bg-surface-50 transition-colors"
                onClick={() => setExpandedReview(expandedReview === review.id ? null : review.id)}
              >
                <div className="flex items-start gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1.5 flex-wrap">
                      <StarRating rating={review.rating} size="sm" />
                      {review.reply && <StatusBadge status={review.reply.status} />}
                      {!review.reply && (
                        <span className="badge bg-zinc-100 text-zinc-500">No reply yet</span>
                      )}
                    </div>

                    <p className="text-sm text-zinc-700 leading-relaxed">
                      {expandedReview === review.id
                        ? review.review_text
                        : review.review_text.slice(0, 160) + (review.review_text.length > 160 ? "…" : "")}
                    </p>

                    <div className="flex items-center gap-2 mt-2">
                      <span className="text-xs font-medium text-zinc-600">
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

                  <ChevronDown
                    className={clsx(
                      "w-4 h-4 text-zinc-400 flex-shrink-0 transition-transform",
                      expandedReview === review.id && "rotate-180"
                    )}
                  />
                </div>
              </div>

              {/* AI Reply Section */}
              {expandedReview === review.id && review.reply && (
                <div className="border-t border-zinc-100 bg-gradient-to-b from-surface-50 to-white px-5 py-4">
                  <div className="flex items-center gap-2 mb-3">
                    <Sparkles className="w-4 h-4 text-brand-500" />
                    <span className="text-xs font-semibold text-brand-600 uppercase tracking-wide">
                      AI Reply Suggestion
                    </span>
                  </div>

                  {editMode[review.id] ? (
                    <textarea
                      className="input text-sm leading-relaxed h-28 resize-none mb-3"
                      value={editingReply[review.id] ?? review.reply.reply_text}
                      onChange={(e) =>
                        setEditingReply((prev) => ({ ...prev, [review.id]: e.target.value }))
                      }
                    />
                  ) : (
                    <p className="text-sm text-zinc-700 leading-relaxed mb-3 bg-white rounded-xl p-3 border border-zinc-100">
                      {review.reply.reply_text}
                    </p>
                  )}

                  {review.reply.status === "pending" && (
                    <div className="flex items-center gap-2 flex-wrap">
                      <button
                        onClick={() => handleApprove(review.id, review.reply!.id)}
                        disabled={actionLoading[review.reply.id]}
                        className="btn-primary flex items-center gap-1.5 text-sm py-2 px-4"
                      >
                        {actionLoading[review.reply.id] ? (
                          <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                        ) : (
                          <Check className="w-3.5 h-3.5" />
                        )}
                        {editMode[review.id] ? "Save & Approve" : "Approve"}
                      </button>

                      <button
                        onClick={() => toggleEdit(review.id, review.reply!.reply_text)}
                        className="btn-secondary flex items-center gap-1.5 text-sm py-2 px-4"
                      >
                        <Edit3 className="w-3.5 h-3.5" />
                        {editMode[review.id] ? "Cancel Edit" : "Edit"}
                      </button>

                      <button
                        onClick={() => handleCopy(review.reply!.reply_text, review.reply!.id)}
                        className="btn-ghost flex items-center gap-1.5 text-sm py-2 px-3"
                      >
                        <Copy className="w-3.5 h-3.5" />
                        {copiedId === review.reply.id ? "Copied!" : "Copy"}
                      </button>

                      <button
                        onClick={() => handleReject(review.id, review.reply!.id)}
                        className="btn-ghost flex items-center gap-1.5 text-sm py-2 px-3 text-red-500 hover:bg-red-50"
                      >
                        <X className="w-3.5 h-3.5" />
                        Reject
                      </button>

                      <button
                        onClick={() => handleRegenerate(review.id)}
                        disabled={actionLoading[review.id]}
                        className="btn-ghost flex items-center gap-1.5 text-sm py-2 px-3 ml-auto"
                      >
                        <RefreshCw className={clsx("w-3.5 h-3.5", actionLoading[review.id] && "animate-spin")} />
                        Regenerate
                      </button>
                    </div>
                  )}

                  {review.reply.status === "approved" && (
                    <div className="flex items-center gap-3">
                      <button
                        onClick={() => handleCopy(review.reply!.reply_text, review.reply!.id)}
                        className="btn-secondary flex items-center gap-1.5 text-sm py-2 px-4"
                      >
                        <Copy className="w-3.5 h-3.5" />
                        {copiedId === review.reply.id ? "Copied!" : "Copy Reply"}
                      </button>
                      <span className="text-xs text-zinc-400">
                        Approved — paste this reply into Google Maps
                      </span>
                    </div>
                  )}

                  {review.reply.status === "rejected" && (
                    <button
                      onClick={() => handleRegenerate(review.id)}
                      className="btn-secondary flex items-center gap-1.5 text-sm py-2 px-4"
                    >
                      <Sparkles className="w-3.5 h-3.5" />
                      Generate New Reply
                    </button>
                  )}
                </div>
              )}

              {/* No reply yet */}
              {expandedReview === review.id && !review.reply && (
                <div className="border-t border-zinc-100 px-5 py-4 bg-surface-50">
                  <button
                    onClick={() => handleRegenerate(review.id)}
                    disabled={actionLoading[review.id]}
                    className="btn-primary flex items-center gap-2 text-sm"
                  >
                    {actionLoading[review.id] ? (
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    ) : (
                      <Sparkles className="w-4 h-4" />
                    )}
                    Generate AI Reply
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}