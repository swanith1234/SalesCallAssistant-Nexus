import { useState } from "react";
import { Phone, Mic, MicOff, PhoneOff, Lightbulb, Package, MessageSquare } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import Navbar from "@/components/Navbar";
import { Badge } from "@/components/ui/badge";

const LiveCall = () => {
  const [isMuted, setIsMuted] = useState(false);
  const [sentiment, setSentiment] = useState<"happy" | "neutral" | "confused" | "upset">("neutral");

  const sentimentConfig = {
    happy: { color: "bg-green-500", label: "Happy", emoji: "😊" },
    neutral: { color: "bg-blue-500", label: "Neutral", emoji: "😐" },
    confused: { color: "bg-yellow-500", label: "Confused", emoji: "🤔" },
    upset: { color: "bg-red-500", label: "Upset", emoji: "😟" },
  };

  const suggestions = [
    {
      type: "question",
      icon: MessageSquare,
      text: "Ask about their current pain points",
    },
    {
      type: "objection",
      icon: Lightbulb,
      text: "Address pricing concerns by highlighting ROI",
    },
    {
      type: "product",
      icon: Package,
      text: "Recommend Premium Plan based on their needs",
    },
  ];

  const transcript = [
    { speaker: "Customer", text: "I'm looking for a solution that can help our team...", time: "00:12" },
    { speaker: "You", text: "I understand. Can you tell me more about your current challenges?", time: "00:18" },
    { speaker: "Customer", text: "We're struggling with managing our sales pipeline effectively.", time: "00:25" },
  ];

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      
      <main className="container mx-auto px-4 pt-24 pb-12">
        <div className="mb-6 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="relative">
              <div className={`w-4 h-4 rounded-full ${sentimentConfig[sentiment].color} animate-pulse-glow`} />
              <div className={`absolute inset-0 ${sentimentConfig[sentiment].color} opacity-50 blur-md animate-pulse-glow`} />
            </div>
            <div>
              <h1 className="text-2xl font-bold">Live Call</h1>
              <p className="text-sm text-muted-foreground">
                Customer: John Doe • Duration: 05:23
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="text-lg px-4 py-2 border-primary/40">
              {sentimentConfig[sentiment].emoji} {sentimentConfig[sentiment].label}
            </Badge>
          </div>
        </div>

        <div className="grid lg:grid-cols-3 gap-6">
          {/* Main Call Area */}
          <div className="lg:col-span-2 space-y-6">
            {/* Waveform Visualization */}
            <Card className="p-8 bg-card/40 backdrop-blur-md border-primary/20">
              <div className="flex items-center justify-center h-48 relative">
                <div className="absolute inset-0 flex items-center justify-center gap-1">
                  {[...Array(40)].map((_, i) => (
                    <div
                      key={i}
                      className="w-1 bg-primary rounded-full animate-pulse-glow"
                      style={{
                        height: `${Math.random() * 100 + 20}%`,
                        animationDelay: `${i * 50}ms`,
                      }}
                    />
                  ))}
                </div>
                <div className="relative z-10 text-center">
                  <Phone className="w-12 h-12 text-primary mx-auto mb-2" />
                  <p className="text-sm text-muted-foreground">Call in progress...</p>
                </div>
              </div>
              
              <div className="flex items-center justify-center gap-4 mt-8">
                <Button
                  variant={isMuted ? "destructive" : "glass"}
                  size="icon"
                  className="w-12 h-12 rounded-full"
                  onClick={() => setIsMuted(!isMuted)}
                >
                  {isMuted ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
                </Button>
                <Button
                  variant="destructive"
                  size="icon"
                  className="w-14 h-14 rounded-full"
                >
                  <PhoneOff className="w-6 h-6" />
                </Button>
              </div>
            </Card>

            {/* Transcript */}
            <Card className="p-6 bg-card/40 backdrop-blur-md border-primary/20">
              <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                <MessageSquare className="w-5 h-5 text-primary" />
                Live Transcript
              </h2>
              
              <div className="space-y-4 max-h-96 overflow-y-auto">
                {transcript.map((entry, index) => (
                  <div
                    key={index}
                    className={`p-3 rounded-lg ${
                      entry.speaker === "You"
                        ? "bg-primary/10 ml-8"
                        : "bg-muted/30 mr-8"
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium text-primary">
                        {entry.speaker}
                      </span>
                      <span className="text-xs text-muted-foreground">{entry.time}</span>
                    </div>
                    <p className="text-sm">{entry.text}</p>
                  </div>
                ))}
              </div>
            </Card>
          </div>

          {/* AI Suggestions Panel */}
          <div className="space-y-6">
            <Card className="p-6 bg-card/40 backdrop-blur-md border-primary/20">
              <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                <Lightbulb className="w-5 h-5 text-primary" />
                AI Suggestions
              </h2>
              
              <div className="space-y-4">
                {suggestions.map((suggestion, index) => (
                  <div
                    key={index}
                    className="p-4 rounded-lg bg-muted/30 border border-primary/10 hover:border-primary/30 transition-all duration-300 cursor-pointer group"
                  >
                    <div className="flex items-start gap-3">
                      <div className="p-2 rounded-lg bg-primary/10 group-hover:bg-primary/20 transition-colors">
                        <suggestion.icon className="w-4 h-4 text-primary" />
                      </div>
                      <p className="text-sm flex-1 group-hover:text-primary-glow transition-colors">
                        {suggestion.text}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </Card>

            {/* Quick Stats */}
            <Card className="p-6 bg-card/40 backdrop-blur-md border-primary/20">
              <h2 className="text-xl font-bold mb-4">Call Stats</h2>
              
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-muted-foreground">Talk Time</span>
                    <span className="font-medium">65%</span>
                  </div>
                  <div className="h-2 bg-muted/30 rounded-full overflow-hidden">
                    <div className="h-full bg-primary w-[65%] rounded-full" />
                  </div>
                </div>
                
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-muted-foreground">Engagement</span>
                    <span className="font-medium">High</span>
                  </div>
                  <div className="h-2 bg-muted/30 rounded-full overflow-hidden">
                    <div className="h-full bg-green-500 w-[85%] rounded-full" />
                  </div>
                </div>
              </div>
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
};

export default LiveCall;
