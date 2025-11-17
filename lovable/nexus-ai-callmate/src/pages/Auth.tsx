import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card } from "@/components/ui/card";
import { Zap, Mail, Lock } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useToast } from "@/hooks/use-toast";

const Auth = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const navigate = useNavigate();
  const { toast } = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const endpoint = isLogin ? "/auth/login" : "/auth/register";

    try {
      const res = await fetch(`http://localhost:8000${endpoint}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email,
          password,
          full_name: email.split("@")[0], // used for register
        }),
      });

      if (!res.ok) {
        toast({
          title: "Error",
          description: "Invalid credentials",
          variant: "destructive",
        });
        return;
      }

      const data = await res.json();

      // 🔥 Save JWT + user info
      localStorage.setItem("auth", JSON.stringify(data));

      toast({
        title: "Success",
        description: "Redirecting to dashboard...",
      });

      setTimeout(() => navigate("/dashboard"), 800);
    } catch (err) {
      toast({
        title: "Error",
        description: "Something went wrong",
      });
    }
  };

  const handleGoogleAuth = () => {
    toast({
      title: "Google Sign-In",
      description: "Google OAuth integration ready",
    });
  };

  return (
    <div className="min-h-screen flex items-center justify-center relative overflow-hidden">
      <div className="absolute inset-0 bg-gradient-glow opacity-50" />

      <Card className="w-full max-w-md mx-4 p-8 bg-card/40 backdrop-blur-xl border-primary/20">
        <div className="text-center mb-8">
          <Zap className="w-12 h-12 text-primary mx-auto animate-pulse-glow" />
          <h1 className="text-3xl font-bold bg-gradient-primary bg-clip-text text-transparent">
            Nexus
          </h1>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-2">
            <Label htmlFor="email" className="flex items-center gap-2">
              <Mail className="w-4 h-4" /> Email
            </Label>
            <Input
              id="email"
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="password" className="flex items-center gap-2">
              <Lock className="w-4 h-4" /> Password
            </Label>
            <Input
              id="password"
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          <Button type="submit" className="w-full" size="lg">
            {isLogin ? "Sign In" : "Create Account"}
          </Button>
        </form>

        <div className="mt-6 text-center text-sm">
          <span className="text-muted-foreground">
            {isLogin ? "Don't have an account?" : "Already have an account?"}
          </span>{" "}
          <button
            type="button"
            onClick={() => setIsLogin(!isLogin)}
            className="text-primary font-medium"
          >
            {isLogin ? "Sign up" : "Sign in"}
          </button>
        </div>
      </Card>
    </div>
  );
};

export default Auth;
