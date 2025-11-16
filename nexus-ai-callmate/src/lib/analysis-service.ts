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

// NEW: Session/Call History interfaces
export interface CallSession {
  session_id: string;
  timestamp: string;
  total_messages: number;
  latest_analysis: Analysis | null;
  messages: Message[];
}

export interface ConversationsResponse {
  sessions: Array<{
    room_id: string;
    count: number;
  }>;
}

const API_BASE = "http://localhost:8000";

/**
 * Fetch the latest sentiment analysis for a room
 */
export async function fetchLatestAnalysis(
  roomId: string
): Promise<AnalysisResponse> {
  const res = await fetch(`${API_BASE}/analysis/${roomId}`);
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

/**
 * NEW: Fetch all conversations (call history)
 */
export async function fetchConversations(): Promise<ConversationsResponse> {
  const res = await fetch(`${API_BASE}/conversations`);
  if (!res.ok) {
    throw new Error(`Failed to fetch conversations: ${res.statusText}`);
  }
  return (await res.json()) as ConversationsResponse;
}

/**
 * NEW: Fetch a specific saved session by ID
 */
export async function fetchSession(sessionId: string): Promise<CallSession> {
  const res = await fetch(`${API_BASE}/session/${sessionId}`);
  if (!res.ok) {
    throw new Error(`Failed to fetch session: ${res.statusText}`);
  }
  return (await res.json()) as CallSession;
}