// src/lib/livekit-service.ts

export interface TokenResponse {
  token: string;
  url: string;
  room: string;
  userId: string;
}

export const getLiveKitToken = async (
  roomName: string,
  participantName: string,
  userId: string
): Promise<TokenResponse> => {
  const response = await fetch("http://localhost:8000/get-token", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      room_name: roomName,
      participant_name: participantName,
      userId, // 🔥 SEND REAL USER ID
    }),
  });

  if (!response.ok) {
    throw new Error(`Failed to get token: ${response.statusText}`);
  }

  return response.json();
};
