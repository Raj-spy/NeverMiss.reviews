"use client";

import { useEffect, useState } from "react";
import { businessApi } from "@/lib/api";
import { Business } from "@/types";
import {
  Plus, Building2, ExternalLink, Trash2,
  RefreshCw, X, Star, AlertCircle, CheckCircle2
} from "lucide-react";
import { formatDistanceToNow } from "date-fns";

function validateMapsUrl(url: string): { valid: boolean; message: string } {
  if (!url) return { valid: false, message: "" };
  const lower = url.toLowerCase();
  if (lower.includes("share.google") || lower.includes("maps.app.goo.gl")) {
    return { valid: false, message: "❌ Share links not supported. Copy URL from browser address bar." };
  }
  if (lower.includes("google.com/maps") || lower.includes("maps.google.com") || lower.includes("goo.gl/maps")) {
    return { valid: true, message: "✅ Valid Google Maps URL" };
  }
  return { valid: false, message: "❌ Invalid URL. Must be a google.com/maps link." };
}

export default function BusinessPage() {
  const [businesses, setBusinesses] = useState<Business[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState({ business_name: "", google_maps_url: "", description: "" });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [refreshingId, setRefreshingId] = useState<string | null>(null);
  const [refreshSuccess, setRefreshSuccess] = useState<string | null>(null);

  const urlValidation = validateMapsUrl(form.google_maps_url);

  const load = async () => {
    try {
      const res = await businessApi.list();
      setBusinesses(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!urlValidation.valid) {
      setError("Please enter a valid Google Maps URL from your browser address bar.");
      return;
    }
    setSubmitting(true);
    setError("");
    try {
      await businessApi.create(form);
      setShowModal(false);
      setForm({ business_name: "", google_maps_url: "", description: "" });
      load();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to add business");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id: string, name: string) => {
    if (!confirm(`Delete "${name}"? This will remove all associated reviews and replies.`)) return;
    try {
      await businessApi.delete(id);
      setBusinesses((prev) => prev.filter((b) => b.id !== id));
    } catch (err) {
      alert("Failed to delete business");
    }
  };

  const handleRefresh = async (id: string) => {
    setRefreshingId(id);
    setRefreshSuccess(null);
    try {
      await businessApi.refresh(id);
      setRefreshSuccess(id);
      setTimeout(() => setRefreshSuccess(null), 3000);
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed to trigger refresh");
    } finally {
      setRefreshingId(null);
    }
  };

  const closeModal = () => {
    setShowModal(false);
    setError("");
    setForm({ business_name: "", google_maps_url: "", description: "" });
  };

  // Fixed: Added missing closing brace here

  return (
    <div className="space-y-6 max-w-5xl">

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-3xl font-bold text-zinc-900">Businesses</h1>
          <p className="text-zinc-500 mt-1">Manage your Google Maps business profiles</p>
        </div>
        <button onClick={() => setShowModal(true)} className="btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" /> Add Business
        </button>
      </div>

      {/* Business Grid */}
      {loading ? (
        <div className="flex items-center justify-center h-48">
          <div className="w-8 h-8 border-[3px] border-brand-500 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : businesses.length === 0 ? (
        <div className="card p-16 text-center">
          <Building2 className="w-12 h-12 text-zinc-300 mx-auto mb-3" />
          <h3 className="font-display font-semibold text-zinc-900 mb-1">No businesses yet</h3>
          <p className="text-zinc-500 text-sm mb-4">Add your first business to start monitoring Google reviews</p>
          <button onClick={() => setShowModal(true)} className="btn-primary inline-flex items-center gap-2">
            <Plus className="w-4 h-4" /> Add Business
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {businesses.map((biz) => (
            <div key={biz.id} className="card p-5 hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between mb-3">
                <div className="w-10 h-10 bg-brand-50 rounded-xl flex items-center justify-center">
                  <Building2 className="w-5 h-5 text-brand-600" />
                </div>
                <div className="flex items-center gap-1">
                  <button
                    onClick={() => handleRefresh(biz.id)}
                    disabled={refreshingId === biz.id}
                    className="p-1.5 rounded-lg text-zinc-400 hover:text-brand-600 hover:bg-brand-50 transition-colors"
                    title="Check for new reviews"
                  >
                    <RefreshCw className={`w-3.5 h-3.5 ${refreshingId === biz.id ? "animate-spin text-brand-500" : ""}`} />
                  </button>
                  
                  {/* Fixed: Properly wrapped ExternalLink in <a> tag */}
                  <a
                    href={biz.google_maps_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="p-1.5 rounded-lg text-zinc-400 hover:text-brand-600 hover:bg-brand-50 transition-colors"
                    title="View on Google Maps"
                  >
                    <ExternalLink className="w-3.5 h-3.5" />
                  </a>
                  
                  <button
                    onClick={() => handleDelete(biz.id, biz.business_name)}
                    className="p-1.5 rounded-lg text-zinc-400 hover:text-red-600 hover:bg-red-50 transition-colors"
                    title="Delete business"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              <h3 className="font-display font-semibold text-zinc-900 mb-1">{biz.business_name}</h3>
              {biz.description && (
                <p className="text-xs text-zinc-500 mb-3 line-clamp-2">{biz.description}</p>
              )}

              {refreshSuccess === biz.id && (
                <div className="flex items-center gap-1.5 text-xs text-green-600 bg-green-50 rounded-lg px-2.5 py-1.5 mb-2">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  Checking for new reviews in background...
                </div>
              )}

              <div className="flex items-center gap-3 mt-3 pt-3 border-t border-zinc-100">
                <div className="flex items-center gap-1">
                  <Star className="w-3.5 h-3.5 fill-amber-400 text-amber-400" />
                  <span className="text-sm font-medium text-zinc-700">
                    {biz.avg_rating ? biz.avg_rating.toFixed(1) : "—"}
                  </span>
                </div>
                <span className="text-zinc-200">·</span>
                <span className="text-xs text-zinc-500">{biz.review_count} reviews</span>
                <span className="text-zinc-200">·</span>
                <span className="text-xs text-zinc-400">
                  Added {formatDistanceToNow(new Date(biz.created_at), { addSuffix: true })}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Add Business Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/30 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-md">
            <div className="flex items-center justify-between px-6 py-4 border-b border-zinc-100">
              <h2 className="font-display font-semibold text-zinc-900">Add Business</h2>
              <button onClick={closeModal} className="btn-ghost p-2">
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCreate} className="p-6 space-y-4">
              {error && (
                <div className="flex items-start gap-2 bg-red-50 border border-red-100 text-red-700 text-sm px-4 py-3 rounded-xl">
                  <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                  {error}
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-zinc-700 mb-1.5">Business Name *</label>
                <input
                  className="input"
                  placeholder="e.g. Godwit Cafe"
                  value={form.business_name}
                  onChange={(e) => setForm({ ...form, business_name: e.target.value })}
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-zinc-700 mb-1.5">Google Maps URL *</label>
                <input
                  className={`input ${
                    form.google_maps_url && !urlValidation.valid
                      ? "border-red-300 focus:ring-red-200"
                      : form.google_maps_url && urlValidation.valid
                      ? "border-green-300 focus:ring-green-200"
                      : ""
                  }`}
                  placeholder="https://www.google.com/maps/place/..."
                  value={form.google_maps_url}
                  onChange={(e) => setForm({ ...form, google_maps_url: e.target.value })}
                  required
                />
                {form.google_maps_url && (
                  <p className={`text-xs mt-1.5 ${urlValidation.valid ? "text-green-600" : "text-red-500"}`}>
                    {urlValidation.message}
                  </p>
                )}
                <div className="mt-2 bg-zinc-50 rounded-xl p-3">
                  <p className="text-xs font-medium text-zinc-600 mb-1">How to get the correct URL:</p>
                  <ol className="text-xs text-zinc-500 space-y-0.5 list-decimal list-inside">
                    <li>Open <strong>maps.google.com</strong> in your browser</li>
                    <li>Search for your business and click on it</li>
                    <li>Copy the URL from the <strong>browser address bar</strong></li>
                  </ol>
                  <p className="text-xs text-red-400 mt-1.5">⚠️ Do not use the Share button — those links will not work</p>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-zinc-700 mb-1.5">
                  Description <span className="text-zinc-400 font-normal">(optional)</span>
                </label>
                <textarea
                  className="input resize-none h-20"
                  placeholder="Brief description of your business..."
                  value={form.description}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                />
              </div>

              <div className="flex gap-3 pt-2">
                <button type="button" onClick={closeModal} className="btn-secondary flex-1">
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn-primary flex-1"
                  disabled={submitting || !urlValidation.valid}
                >
                  {submitting ? (
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mx-auto" />
                  ) : (
                    "Add Business"
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
}
