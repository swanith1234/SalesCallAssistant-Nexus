import { LiveKitRoom } from "@livekit/components-react";

export const LIVEKIT_URL = import.meta.env.VITE_LIVEKIT_URL;
export const LIVEKIT_API_KEY = import.meta.env.VITE_LIVEKIT_API_KEY;

export const getLiveKitConnectionDetails = async () => {
  const response = await fetch("http://127.0.0.1:8000/get-token", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      room_name: `room-${Date.now()}`,
      participant_name: `user-${Date.now()}`,
    }),
  });

  if (!response.ok) {
    throw new Error("Failed to fetch connection details");
  }

  return await response.json();
};
