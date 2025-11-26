// src/lib/analysis-service.ts
export type Sentiment = "positive" | "neutral" | "negative";

export interface Analysis {
  sentiment: Sentiment;
  confidence: number;
  key_points: string[];
  recommendation_to_salesperson: string;
}

export interface AnalysisResponse {
  room_id: string;
  analysis: Analysis | null;
}

export interface Message {
  text: string;
  speaker: "user" | "assistant";
  sent_ts: number;
  received_at: string;
  room_id: string;
}

export interface MessagesResponse {
  room_id: string;
  messages: Message[];
}

const API_BASE = "https://salescallassistant-nexus.onrender.com";

/**
 * Fetch the latest sentiment analysis for a room
 */
export async function fetchLatestAnalysis(
  roomId: string
): Promise<AnalysisResponse> {
  const res = await fetch(`${API_BASE}/analysis/${roomId}`);
  console.log("fetchLatestAnalysis response:", res);
  if (!res.ok) {
    throw new Error(`Failed to fetch analysis: ${res.statusText}`);
  }
  return (await res.json()) as AnalysisResponse;
}

/**
 * Fetch recent messages for a room
 */
export async function fetchMessages(
  roomId: string,
  limit = 50
): Promise<MessagesResponse> {
  const res = await fetch(`${API_BASE}/messages/${roomId}?limit=${limit}`);
  if (!res.ok) {
    throw new Error(`Failed to fetch messages: ${res.statusText}`);
  }
  return (await res.json()) as MessagesResponse;
}