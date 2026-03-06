// frontend/src/types/index.ts

export interface User {
  id: string;
  email: string;
  full_name?: string;
}

export interface Business {
  id: string;
  user_id: string;
  business_name: string;
  google_maps_url: string;
  description?: string;
  created_at: string;
  review_count: number;
  avg_rating?: number;
}

export interface AIReply {
  id: string;
  review_id: string;
  reply_text: string;
  status: "pending" | "approved" | "rejected";
  created_at: string;
  updated_at?: string;
}

export interface Review {
  id: string;
  business_id: string;
  business_name?: string;
  reviewer_name?: string;
  review_text: string;
  rating: number;
  review_date?: string;
  created_at: string;
  processed: boolean;
  reply?: AIReply;
}

export interface Analytics {
  total_reviews: number;
  avg_rating: number;
  pending_replies: number;
  approved_replies: number;
  reviews_this_week: number;
  rating_distribution: Record<string, number>;
}
