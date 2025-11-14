// import { useState } from "react";
// import {
//   Phone,
//   Mic,
//   MicOff,
//   PhoneOff,
//   Lightbulb,
//   Package,
//   MessageSquare,
// } from "lucide-react";
// import { Card } from "@/components/ui/card";
// import { Button } from "@/components/ui/button";
// import Navbar from "@/components/Navbar";
// import { Badge } from "@/components/ui/badge";

// const LiveCall = () => {
//   const [isMuted, setIsMuted] = useState(false);
//   const [sentiment, setSentiment] = useState<
//     "happy" | "neutral" | "confused" | "upset"
//   >("neutral");

//   const sentimentConfig = {
//     happy: { color: "bg-green-500", label: "Happy", emoji: "😊" },
//     neutral: { color: "bg-blue-500", label: "Neutral", emoji: "😐" },
//     confused: { color: "bg-yellow-500", label: "Confused", emoji: "🤔" },
//     upset: { color: "bg-red-500", label: "Upset", emoji: "😟" },
//   };

//   const suggestions = [
//     {
//       type: "question",
//       icon: MessageSquare,
//       text: "Ask about their current pain points",
//     },
//     {
//       type: "objection",
//       icon: Lightbulb,
//       text: "Address pricing concerns by highlighting ROI",
//     },
//     {
//       type: "product",
//       icon: Package,
//       text: "Recommend Premium Plan based on their needs",
//     },
//   ];

//   const transcript = [
//     {
//       speaker: "Customer",
//       text: "I'm looking for a solution that can help our team...",
//       time: "00:12",
//     },
//     {
//       speaker: "You",
//       text: "I understand. Can you tell me more about your current challenges?",
//       time: "00:18",
//     },
//     {
//       speaker: "Customer",
//       text: "We're struggling with managing our sales pipeline effectively.",
//       time: "00:25",
//     },
//   ];

//   return (
//     <div className="min-h-screen bg-background">
//       <Navbar />

//       <main className="container mx-auto px-4 pt-24 pb-12">
//         <div className="mb-6 flex items-center justify-between">
//           <div className="flex items-center gap-4">
//             <div className="relative">
//               <div
//                 className={`w-4 h-4 rounded-full ${sentimentConfig[sentiment].color} animate-pulse-glow`}
//               />
//               <div
//                 className={`absolute inset-0 ${sentimentConfig[sentiment].color} opacity-50 blur-md animate-pulse-glow`}
//               />
//             </div>
//             <div>
//               <h1 className="text-2xl font-bold">Live Call</h1>
//               <p className="text-sm text-muted-foreground">
//                 Customer: John Doe • Duration: 05:23
//               </p>
//             </div>
//           </div>

//           <div className="flex items-center gap-2">
//             <Badge
//               variant="outline"
//               className="text-lg px-4 py-2 border-primary/40"
//             >
//               {sentimentConfig[sentiment].emoji}{" "}
//               {sentimentConfig[sentiment].label}
//             </Badge>
//           </div>
//         </div>

//         <div className="grid lg:grid-cols-3 gap-6">
//           {/* Main Call Area */}
//           <div className="lg:col-span-2 space-y-6">
//             {/* Waveform Visualization */}
//             <Card className="p-8 bg-card/40 backdrop-blur-md border-primary/20">
//               <div className="flex items-center justify-center h-48 relative">
//                 <div className="absolute inset-0 flex items-center justify-center gap-1">
//                   {[...Array(40)].map((_, i) => (
//                     <div
//                       key={i}
//                       className="w-1 bg-primary rounded-full animate-pulse-glow"
//                       style={{
//                         height: `${Math.random() * 100 + 20}%`,
//                         animationDelay: `${i * 50}ms`,
//                       }}
//                     />
//                   ))}
//                 </div>
//                 <div className="relative z-10 text-center">
//                   <Phone className="w-12 h-12 text-primary mx-auto mb-2" />
//                   <p className="text-sm text-muted-foreground">
//                     Call in progress...
//                   </p>
//                 </div>
//               </div>

//               <div className="flex items-center justify-center gap-4 mt-8">
//                 <Button
//                   variant={isMuted ? "destructive" : "glass"}
//                   size="icon"
//                   className="w-12 h-12 rounded-full"
//                   onClick={() => setIsMuted(!isMuted)}
//                 >
//                   {isMuted ? (
//                     <MicOff className="w-5 h-5" />
//                   ) : (
//                     <Mic className="w-5 h-5" />
//                   )}
//                 </Button>
//                 <Button
//                   variant="destructive"
//                   size="icon"
//                   className="w-14 h-14 rounded-full"
//                 >
//                   <PhoneOff className="w-6 h-6" />
//                 </Button>
//               </div>
//             </Card>

//             {/* Transcript */}
//             <Card className="p-6 bg-card/40 backdrop-blur-md border-primary/20">
//               <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
//                 <MessageSquare className="w-5 h-5 text-primary" />
//                 Live Transcript
//               </h2>

//               <div className="space-y-4 max-h-96 overflow-y-auto">
//                 {transcript.map((entry, index) => (
//                   <div
//                     key={index}
//                     className={`p-3 rounded-lg ${
//                       entry.speaker === "You"
//                         ? "bg-primary/10 ml-8"
//                         : "bg-muted/30 mr-8"
//                     }`}
//                   >
//                     <div className="flex items-center justify-between mb-1">
//                       <span className="text-sm font-medium text-primary">
//                         {entry.speaker}
//                       </span>
//                       <span className="text-xs text-muted-foreground">
//                         {entry.time}
//                       </span>
//                     </div>
//                     <p className="text-sm">{entry.text}</p>
//                   </div>
//                 ))}
//               </div>
//             </Card>
//           </div>

//           {/* AI Suggestions Panel */}
//           <div className="space-y-6">
//             <Card className="p-6 bg-card/40 backdrop-blur-md border-primary/20">
//               <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
//                 <Lightbulb className="w-5 h-5 text-primary" />
//                 AI Suggestions
//               </h2>

//               <div className="space-y-4">
//                 {suggestions.map((suggestion, index) => (
//                   <div
//                     key={index}
//                     className="p-4 rounded-lg bg-muted/30 border border-primary/10 hover:border-primary/30 transition-all duration-300 cursor-pointer group"
//                   >
//                     <div className="flex items-start gap-3">
//                       <div className="p-2 rounded-lg bg-primary/10 group-hover:bg-primary/20 transition-colors">
//                         <suggestion.icon className="w-4 h-4 text-primary" />
//                       </div>
//                       <p className="text-sm flex-1 group-hover:text-primary-glow transition-colors">
//                         {suggestion.text}
//                       </p>
//                     </div>
//                   </div>
//                 ))}
//               </div>
//             </Card>

//             {/* Quick Stats */}
//             <Card className="p-6 bg-card/40 backdrop-blur-md border-primary/20">
//               <h2 className="text-xl font-bold mb-4">Call Stats</h2>

//               <div className="space-y-4">
//                 <div>
//                   <div className="flex justify-between text-sm mb-1">
//                     <span className="text-muted-foreground">Talk Time</span>
//                     <span className="font-medium">65%</span>
//                   </div>
//                   <div className="h-2 bg-muted/30 rounded-full overflow-hidden">
//                     <div className="h-full bg-primary w-[65%] rounded-full" />
//                   </div>
//                 </div>

//                 <div>
//                   <div className="flex justify-between text-sm mb-1">
//                     <span className="text-muted-foreground">Engagement</span>
//                     <span className="font-medium">High</span>
//                   </div>
//                   <div className="h-2 bg-muted/30 rounded-full overflow-hidden">
//                     <div className="h-full bg-green-500 w-[85%] rounded-full" />
//                   </div>
//                 </div>
//               </div>
//             </Card>
//           </div>
//         </div>
//       </main>
//     </div>
//   );
// };

// export default LiveCall;
// src/pages/LiveCall.tsx

// import { useState, useEffect, useRef } from "react";
// import { Room, RoomEvent, Track } from "livekit-client";
// import { Mic, MicOff, Phone, PhoneOff, Loader2 } from "lucide-react";
// import { Button } from "@/components/ui/button";
// import {
//   Card,
//   CardContent,
//   CardDescription,
//   CardHeader,
//   CardTitle,
// } from "@/components/ui/card";
// import { Alert, AlertDescription } from "@/components/ui/alert";
// import { Badge } from "@/components/ui/badge";
// import { getLiveKitToken } from "@/lib/livekit-service";
// import { useToast } from "@/hooks/use-toast";

// export default function LiveCall() {
//   const [isConnected, setIsConnected] = useState(false);
//   const [isConnecting, setIsConnecting] = useState(false);
//   const [isMuted, setIsMuted] = useState(false);
//   const [status, setStatus] = useState("Ready");
//   const [roomName, setRoomName] = useState("");

//   const roomRef = useRef<Room | null>(null);
//   const audioElementRef = useRef<HTMLAudioElement | null>(null);
//   const { toast } = useToast();

//   const connectToRoom = async () => {
//     try {
//       setIsConnecting(true);
//       setStatus("Connecting...");

//       // Generate unique room and participant names
//       const newRoomName = `room-${Date.now()}`;
//       const participantName = `user-${Date.now()}`;
//       setRoomName(newRoomName);

//       // Get token from backend
//       const { token, url } = await getLiveKitToken(
//         newRoomName,
//         participantName
//       );

//       // Create and configure room
//       const room = new Room({
//         adaptiveStream: true,
//         dynacast: true,
//       });

//       roomRef.current = room;

//       // Handle incoming audio from agent
//       room.on(RoomEvent.TrackSubscribed, (track, publication, participant) => {
//         console.log(
//           "Track subscribed:",
//           track.kind,
//           "from",
//           participant.identity
//         );
//         if (track.kind === Track.Kind.Audio) {
//           const audioElement = track.attach();
//           audioElementRef.current = audioElement;
//           document.body.appendChild(audioElement);
//           audioElement
//             .play()
//             .catch((err) => console.error("Audio play error:", err));
//         }
//       });

//       // Handle connection state
//       room.on(RoomEvent.Connected, () => {
//         setIsConnected(true);
//         setIsConnecting(false);
//         setStatus("Connected");
//         toast({
//           title: "Connected!",
//           description: "You're now connected to the AI assistant.",
//         });
//       });

//       room.on(RoomEvent.Disconnected, () => {
//         setIsConnected(false);
//         setIsConnecting(false);
//         setStatus("Disconnected");
//         toast({
//           title: "Disconnected",
//           description: "Call ended.",
//           variant: "destructive",
//         });
//       });

//       room.on(RoomEvent.Reconnecting, () => {
//         setStatus("Reconnecting...");
//       });

//       room.on(RoomEvent.Reconnected, () => {
//         setStatus("Connected");
//       });

//       // Connect to LiveKit
//       await room.connect(url, token);

//       // Enable microphone
//       await room.localParticipant.setMicrophoneEnabled(true);
//     } catch (error) {
//       console.error("Connection error:", error);
//       setIsConnecting(false);
//       setStatus("Connection failed");
//       toast({
//         title: "Connection Error",
//         description:
//           error instanceof Error ? error.message : "Failed to connect",
//         variant: "destructive",
//       });
//     }
//   };

//   const disconnect = async () => {
//     if (roomRef.current) {
//       await roomRef.current.disconnect();
//       roomRef.current = null;
//       setIsConnected(false);
//       setStatus("Disconnected");

//       // Clean up audio element
//       if (audioElementRef.current) {
//         audioElementRef.current.remove();
//         audioElementRef.current = null;
//       }
//     }
//   };

//   const toggleMute = async () => {
//     if (roomRef.current && roomRef.current.localParticipant) {
//       const enabled = !isMuted;
//       await roomRef.current.localParticipant.setMicrophoneEnabled(enabled);
//       setIsMuted(!enabled);
//       toast({
//         description: enabled ? "Microphone unmuted" : "Microphone muted",
//       });
//     }
//   };

//   useEffect(() => {
//     return () => {
//       disconnect();
//     };
//   }, []);

//   return (
//     <div className="container mx-auto p-6 max-w-4xl">
//       <Card className="shadow-lg">
//         <CardHeader className="text-center">
//           <CardTitle className="text-3xl font-bold">
//             AI Voice Assistant
//           </CardTitle>
//           <CardDescription className="text-lg">
//             Talk to our AI assistant about Educational AI & ML Courses
//           </CardDescription>
//         </CardHeader>

//         <CardContent className="space-y-6">
//           {/* Status Section */}
//           <div className="bg-secondary/20 rounded-lg p-4 text-center">
//             <p className="text-sm font-medium text-muted-foreground mb-2">
//               Status
//             </p>
//             <div className="flex items-center justify-center gap-2">
//               {isConnecting && <Loader2 className="animate-spin h-5 w-5" />}
//               {isConnected && !isConnecting && (
//                 <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse" />
//               )}
//               <Badge
//                 variant={isConnected ? "default" : "secondary"}
//                 className="text-base"
//               >
//                 {status}
//               </Badge>
//             </div>
//             {roomName && (
//               <p className="text-xs text-muted-foreground mt-2">
//                 Room: {roomName}
//               </p>
//             )}
//           </div>

//           {/* Connection Controls */}
//           <div className="flex gap-3">
//             {!isConnected ? (
//               <Button
//                 onClick={connectToRoom}
//                 disabled={isConnecting}
//                 className="flex-1 h-14 text-lg"
//                 size="lg"
//               >
//                 {isConnecting ? (
//                   <>
//                     <Loader2 className="mr-2 h-5 w-5 animate-spin" />
//                     Connecting...
//                   </>
//                 ) : (
//                   <>
//                     <Phone className="mr-2 h-5 w-5" />
//                     Start Call
//                   </>
//                 )}
//               </Button>
//             ) : (
//               <>
//                 <Button
//                   onClick={toggleMute}
//                   variant={isMuted ? "destructive" : "default"}
//                   className="flex-1 h-14 text-lg"
//                   size="lg"
//                 >
//                   {isMuted ? (
//                     <>
//                       <MicOff className="mr-2 h-5 w-5" />
//                       Unmute
//                     </>
//                   ) : (
//                     <>
//                       <Mic className="mr-2 h-5 w-5" />
//                       Mute
//                     </>
//                   )}
//                 </Button>

//                 <Button
//                   onClick={disconnect}
//                   variant="destructive"
//                   className="flex-1 h-14 text-lg"
//                   size="lg"
//                 >
//                   <PhoneOff className="mr-2 h-5 w-5" />
//                   End Call
//                 </Button>
//               </>
//             )}
//           </div>

//           {/* Active Call Indicator */}
//           {isConnected && (
//             <Alert>
//               <AlertDescription className="flex items-center justify-center gap-2">
//                 <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
//                 <span>
//                   {isMuted
//                     ? "Microphone muted"
//                     : "Microphone active - Speak now"}
//                 </span>
//               </AlertDescription>
//             </Alert>
//           )}

//           {/* Instructions */}
//           <Card className="bg-muted/50">
//             <CardHeader>
//               <CardTitle className="text-lg">How to use</CardTitle>
//             </CardHeader>
//             <CardContent className="space-y-2 text-sm">
//               <div className="flex gap-2">
//                 <span className="font-semibold">1.</span>
//                 <span>Click "Start Call" to connect with the AI assistant</span>
//               </div>
//               <div className="flex gap-2">
//                 <span className="font-semibold">2.</span>
//                 <span>Speak naturally - the AI will listen and respond</span>
//               </div>
//               <div className="flex gap-2">
//                 <span className="font-semibold">3.</span>
//                 <span>Use "Mute" button to pause your microphone</span>
//               </div>
//               <div className="flex gap-2">
//                 <span className="font-semibold">4.</span>
//                 <span>Click "End Call" when you're finished</span>
//               </div>
//             </CardContent>
//           </Card>

//           {/* Troubleshooting */}
//           <Alert variant="default" className="bg-blue-50">
//             <AlertDescription className="text-sm">
//               <p className="font-semibold mb-2">Troubleshooting:</p>
//               <ul className="list-disc list-inside space-y-1 text-xs">
//                 <li>
//                   Ensure your agent is running:{" "}
//                   <code className="bg-gray-200 px-1 rounded">
//                     python agent.py dev
//                   </code>
//                 </li>
//                 <li>
//                   Token endpoint should be at:{" "}
//                   <code className="bg-gray-200 px-1 rounded">
//                     http://localhost:8000
//                   </code>
//                 </li>
//                 <li>Check browser microphone permissions</li>
//                 <li>Make sure LiveKit server is running</li>
//               </ul>
//             </AlertDescription>
//           </Alert>
//         </CardContent>
//       </Card>
//     </div>
//   );
// }
// src/pages/LiveCall.tsx
import { useState, useEffect, useRef } from "react";
import { Room, RoomEvent, Track } from "livekit-client";
import {
  Mic,
  MicOff,
  Phone,
  PhoneOff,
  Loader2,
  Lightbulb,
  MessageSquare,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { getLiveKitToken } from "@/lib/livekit-service";
import { useToast } from "@/hooks/use-toast";
import {
  fetchLatestAnalysis,
  fetchMessages,
  Analysis,
  Message,
} from "@/lib/analysis-service";

type SentimentUi = {
  label: string;
  emoji: string;
  badgeVariant: "default" | "secondary" | "destructive" | "outline";
  pulseColor: string;
};

const SENTIMENT_UI: Record<string, SentimentUi> = {
  positive: {
    label: "Positive",
    emoji: "😊",
    badgeVariant: "default",
    pulseColor: "bg-green-500",
  },
  neutral: {
    label: "Neutral",
    emoji: "😐",
    badgeVariant: "secondary",
    pulseColor: "bg-blue-500",
  },
  negative: {
    label: "Negative",
    emoji: "😟",
    badgeVariant: "destructive",
    pulseColor: "bg-red-500",
  },
};

export default function LiveCall() {
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [status, setStatus] = useState("Ready");
  const [roomName, setRoomName] = useState("");

  // NEW: analysis + transcript state
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);

  const roomRef = useRef<Room | null>(null);
  const audioElementRef = useRef<HTMLAudioElement | null>(null);
  const pollTimerRef = useRef<number | null>(null);
  const { toast } = useToast();

  const startPolling = (roomId: string) => {
    // poll every 1.5s
    const tick = async () => {
      try {
        const [a, m] = await Promise.allSettled([
          fetchLatestAnalysis(roomId),
          fetchMessages(roomId, 60),
        ]);

        if (a.status === "fulfilled") setAnalysis(a.value.analysis);
        if (m.status === "fulfilled") setMessages(m.value.messages);
      } catch (_) {}
    };
    // first pull immediately
    tick();
    pollTimerRef.current = window.setInterval(tick, 1500);
  };

  const stopPolling = () => {
    if (pollTimerRef.current) {
      clearInterval(pollTimerRef.current);
      pollTimerRef.current = null;
    }
    setAnalysis(null);
    setMessages([]);
  };

  const connectToRoom = async () => {
    try {
      setIsConnecting(true);
      setStatus("Connecting...");

      const newRoomName = `room-${Date.now()}`;
      const participantName = `user-${Date.now()}`;
      setRoomName(newRoomName);

      const { token, url } = await getLiveKitToken(
        newRoomName,
        participantName
      );

      const room = new Room({ adaptiveStream: true, dynacast: true });
      roomRef.current = room;

      room.on(RoomEvent.TrackSubscribed, (track, publication, participant) => {
        if (track.kind === Track.Kind.Audio) {
          const audioElement = track.attach();
          audioElementRef.current = audioElement;
          document.body.appendChild(audioElement);
          audioElement
            .play()
            .catch((err) => console.error("Audio play error:", err));
        }
      });

      room.on(RoomEvent.Connected, () => {
        setIsConnected(true);
        setIsConnecting(false);
        setStatus("Connected");
        toast({
          title: "Connected!",
          description: "You're now connected to the AI assistant.",
        });
        startPolling(newRoomName);
      });

      room.on(RoomEvent.Disconnected, () => {
        setIsConnected(false);
        setIsConnecting(false);
        setStatus("Disconnected");
        toast({
          title: "Disconnected",
          description: "Call ended.",
          variant: "destructive",
        });
        stopPolling();
        // optional: ask backend to persist session
        fetch(`http://localhost:8000/save-session?room_id=${newRoomName}`, {
          method: "POST",
        }).catch(() => {});
      });

      room.on(RoomEvent.Reconnecting, () => setStatus("Reconnecting..."));
      room.on(RoomEvent.Reconnected, () => setStatus("Connected"));

      await room.connect(url, token);
      await room.localParticipant.setMicrophoneEnabled(true);
    } catch (error) {
      console.error("Connection error:", error);
      setIsConnecting(false);
      setStatus("Connection failed");
      toast({
        title: "Connection Error",
        description:
          error instanceof Error ? error.message : "Failed to connect",
        variant: "destructive",
      });
    }
  };

  const disconnect = async () => {
    stopPolling();
    if (roomRef.current) {
      await roomRef.current.disconnect();
      roomRef.current = null;
      setIsConnected(false);
      setStatus("Disconnected");
      if (audioElementRef.current) {
        audioElementRef.current.remove();
        audioElementRef.current = null;
      }
    }
    if (roomName) {
      fetch(`http://localhost:8000/save-session?room_id=${roomName}`, {
        method: "POST",
      }).catch(() => {});
    }
  };

  const toggleMute = async () => {
    if (roomRef.current && roomRef.current.localParticipant) {
      const enable = isMuted;
      await roomRef.current.localParticipant.setMicrophoneEnabled(enable);
      setIsMuted(!enable);
      toast({
        description: enable ? "Microphone unmuted" : "Microphone muted",
      });
    }
  };

  useEffect(() => {
    return () => {
      stopPolling();
      disconnect();
    };
  }, []);

  const sentimentKey = analysis?.sentiment ?? "neutral";
  const s = SENTIMENT_UI[sentimentKey] ?? SENTIMENT_UI["neutral"];

  return (
    <div className="container mx-auto p-6 max-w-6xl">
      <Card className="shadow-lg">
        <CardHeader className="flex items-start justify-between gap-4">
          <div>
            <CardTitle className="text-3xl font-bold">
              AI Voice Assistant
            </CardTitle>
            <CardDescription className="text-lg">
              Talk to our AI assistant about Educational AI & ML Courses
            </CardDescription>
            {roomName && (
              <p className="text-xs text-muted-foreground mt-2">
                Room: {roomName}
              </p>
            )}
          </div>

          {/* Sentiment badge like your mock */}
          <div className="flex items-center gap-3">
            <div className="relative">
              <div
                className={`w-3 h-3 rounded-full ${s.pulseColor} animate-pulse`}
              />
              <div
                className={`absolute inset-0 ${s.pulseColor} opacity-40 blur-sm`}
              />
            </div>
            <Badge variant={s.badgeVariant} className="text-base">
              {s.emoji} {s.label}
              {analysis ? (
                <span className="ml-2 text-xs opacity-75">
                  ({Math.round((analysis.confidence || 0) * 100)}%)
                </span>
              ) : null}
            </Badge>
          </div>
        </CardHeader>

        <CardContent className="space-y-6">
          {/* Status Section */}
          <div className="bg-secondary/20 rounded-lg p-4 text-center">
            <p className="text-sm font-medium text-muted-foreground mb-2">
              Status
            </p>
            <div className="flex items-center justify-center gap-2">
              {isConnecting && <Loader2 className="animate-spin h-5 w-5" />}
              {isConnected && !isConnecting && (
                <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse" />
              )}
              <Badge
                variant={isConnected ? "default" : "secondary"}
                className="text-base"
              >
                {status}
              </Badge>
            </div>
          </div>

          {/* Connection Controls */}
          <div className="flex gap-3">
            {!isConnected ? (
              <Button
                onClick={connectToRoom}
                disabled={isConnecting}
                className="flex-1 h-14 text-lg"
                size="lg"
              >
                {isConnecting ? (
                  <>
                    <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                    Connecting...
                  </>
                ) : (
                  <>
                    <Phone className="mr-2 h-5 w-5" />
                    Start Call
                  </>
                )}
              </Button>
            ) : (
              <>
                <Button
                  onClick={toggleMute}
                  variant={isMuted ? "destructive" : "default"}
                  className="flex-1 h-14 text-lg"
                  size="lg"
                >
                  {isMuted ? (
                    <>
                      <MicOff className="mr-2 h-5 w-5" />
                      Unmute
                    </>
                  ) : (
                    <>
                      <Mic className="mr-2 h-5 w-5" />
                      Mute
                    </>
                  )}
                </Button>
                <Button
                  onClick={disconnect}
                  variant="destructive"
                  className="flex-1 h-14 text-lg"
                  size="lg"
                >
                  <PhoneOff className="mr-2 h-5 w-5" />
                  End Call
                </Button>
              </>
            )}
          </div>

          {isConnected && (
            <Alert>
              <AlertDescription className="flex items-center justify-center gap-2">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                <span>
                  {isMuted
                    ? "Microphone muted"
                    : "Microphone active - Speak now"}
                </span>
              </AlertDescription>
            </Alert>
          )}

          {/* 2-column layout: Transcript + AI Suggestions */}
          <div className="grid lg:grid-cols-3 gap-6">
            {/* Transcript */}
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle className="text-xl flex items-center gap-2">
                  <MessageSquare className="w-5 h-5 text-primary" />
                  Live Transcript
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4 max-h-96 overflow-y-auto">
                  {messages.map((m, idx) => (
                    <div
                      key={idx}
                      className={`p-3 rounded-lg ${
                        m.speaker === "assistant"
                          ? "bg-primary/10 ml-8"
                          : "bg-muted/30 mr-8"
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm font-medium text-primary">
                          {m.speaker === "assistant" ? "Agent" : "You"}
                        </span>
                        <span className="text-xs text-muted-foreground">
                          {new Date(m.sent_ts * 1000).toLocaleTimeString()}
                        </span>
                      </div>
                      <p className="text-sm">{m.text}</p>
                    </div>
                  ))}
                  {messages.length === 0 && (
                    <p className="text-sm text-muted-foreground">
                      Start talking to see the transcript here.
                    </p>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* AI Suggestions */}
            <Card>
              <CardHeader>
                <CardTitle className="text-xl flex items-center gap-2">
                  <Lightbulb className="w-5 h-5 text-primary" />
                  AI Suggestions
                </CardTitle>
                {analysis?.key_points?.length ? (
                  <CardDescription>
                    {analysis.key_points.slice(0, 3).join(" • ")}
                  </CardDescription>
                ) : null}
              </CardHeader>
              <CardContent className="space-y-3">
                {analysis ? (
                  <>
                    <div className="p-4 rounded-lg bg-muted/30 border border-primary/10">
                      <p className="text-sm">
                        {analysis.recommendation_to_salesperson}
                      </p>
                    </div>
                    {analysis.key_points?.map((kp, i) => (
                      <div
                        key={i}
                        className="p-3 rounded-lg bg-muted/20 border"
                      >
                        <p className="text-sm">• {kp}</p>
                      </div>
                    ))}
                  </>
                ) : (
                  <p className="text-sm text-muted-foreground">
                    Suggestions will appear as you speak.
                  </p>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Help */}
          <Alert variant="default" className="bg-blue-50">
            <AlertDescription className="text-sm">
              <p className="font-semibold mb-2">Troubleshooting:</p>
              <ul className="list-disc list-inside space-y-1 text-xs">
                <li>
                  Ensure your agent is running:{" "}
                  <code className="bg-gray-200 px-1 rounded">
                    python agent.py dev
                  </code>
                </li>
                <li>
                  Backend:{" "}
                  <code className="bg-gray-200 px-1 rounded">
                    http://localhost:8000
                  </code>
                </li>
                <li>Check browser microphone permissions</li>
                <li>Make sure LiveKit server is running</li>
              </ul>
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    </div>
  );
}
