import { useEffect, useState } from "react";
import { Phone, TrendingUp, Users, Star, Activity } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import Navbar from "@/components/Navbar";
import { Link } from "react-router-dom";

interface RecentCall {
  id: string;
  customerName: string;
  sentiment: string;
  duration: string;
  rating: number;
}

interface DashboardStats {
  total_calls: number;
  success_rate: number;
  active_users: number;
  avg_rating: number;
  trends: {
    calls: string;
    success_rate: string;
    users: string;
    rating: string;
  };
}

const Dashboard = () => {
  const [recentCalls, setRecentCalls] = useState<RecentCall[]>([]);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [statsLoading, setStatsLoading] = useState(true);

  const statsConfig = [
    {
      label: "Total Calls",
      key: "total_calls",
      icon: Phone,
      trendKey: "calls",
    },
    {
      label: "Success Rate",
      key: "success_rate",
      icon: TrendingUp,
      trendKey: "success_rate",
      suffix: "%",
    },
    {
      label: "Active Users",
      key: "active_users",
      icon: Users,
      trendKey: "users",
    },
    {
      label: "Avg Rating",
      key: "avg_rating",
      icon: Star,
      trendKey: "rating",
    },
  ];

  const emotionColor = (emotion: string) => {
    const colors: Record<string, string> = {
      Happy: "text-green-400",
      Confused: "text-yellow-400",
      Neutral: "text-blue-400",
      Upset: "text-red-400",
    };
    return colors[emotion] || "text-gray-400";
  };

  const getInitials = (name: string) => {
    return name
      .split(" ")
      .map((n) => n[0])
      .join("")
      .toUpperCase();
  };

  const getTrendColor = (trend: string) => {
    if (trend.startsWith("+")) return "text-green-400";
    if (trend.startsWith("-")) return "text-red-400";
    return "text-gray-400";
  };

  useEffect(() => {
    const auth = JSON.parse(localStorage.getItem("auth") || "{}");
    const token = auth?.access_token;

    if (!token) {
      console.error("No authentication token found");
      setStatsLoading(false);
      setLoading(false);
      return;
    }

    // Fetch dashboard stats
    const fetchStats = async () => {
      try {
        const response = await fetch(`http://localhost:8000/dashboard/stats`, {
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        setStats(data);
      } catch (error) {
        console.error("Failed to fetch stats:", error);
      } finally {
        setStatsLoading(false);
      }
    };

    // Fetch recent calls
    const fetchCalls = async () => {
      try {
        const response = await fetch(`http://localhost:8000/recent-calls`, {
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        const mapped = (data.calls || []).map((call: any) => ({
          id: call.id,
          customerName: call.customerName || "Unknown",
          sentiment: call.sentiment,
          duration: call.duration || "0:00",
          rating: call.rating || 3,
        }));

        setRecentCalls(mapped);
      } catch (error) {
        console.error("Failed to fetch calls:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
    fetchCalls();
  }, []);

  return (
    <div className="min-h-screen bg-background">
      <Navbar />

      <main className="container mx-auto px-4 pt-24 pb-12">
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold mb-2 bg-gradient-primary bg-clip-text text-transparent">
              Dashboard
            </h1>
            <p className="text-muted-foreground">
              Overview of your sales performance and recent calls
            </p>
          </div>
          <Link to="/live-call">
            <Button size="lg" className="gap-2">
              <Activity className="w-5 h-5" />
              Start Call
            </Button>
          </Link>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {statsConfig.map((stat, index) => {
            const value = stats
              ? stat.key === "avg_rating"
                ? stats[stat.key as keyof DashboardStats].toFixed(1)
                : stats[stat.key as keyof DashboardStats].toString()
              : "0";

            const trend =
              stats?.trends[stat.trendKey as keyof typeof stats.trends] ||
              "+0%";

            return (
              <Card
                key={stat.label}
                className="p-6 bg-card/40 backdrop-blur-md border-primary/20 hover:border-primary/40 transition-all duration-300 hover:shadow-glow animate-slide-in"
                style={{ animationDelay: `${index * 100}ms` }}
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="p-3 rounded-lg bg-primary/10">
                    <stat.icon className="w-6 h-6 text-primary" />
                  </div>
                  {statsLoading ? (
                    <div className="h-5 w-12 bg-muted/30 rounded animate-pulse" />
                  ) : (
                    <span
                      className={`text-sm font-medium ${getTrendColor(trend)}`}
                    >
                      {trend}
                    </span>
                  )}
                </div>
                {statsLoading ? (
                  <>
                    <div className="h-8 w-16 bg-muted/30 rounded mb-2 animate-pulse" />
                    <div className="h-4 w-24 bg-muted/30 rounded animate-pulse" />
                  </>
                ) : (
                  <>
                    <p className="text-3xl font-bold mb-1">
                      {value}
                      {stat.suffix || ""}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      {stat.label}
                    </p>
                  </>
                )}
              </Card>
            );
          })}
        </div>

        {/* Recent Calls */}
        <Card className="p-6 bg-card/40 backdrop-blur-md border-primary/20">
          <h2 className="text-2xl font-bold mb-6 flex items-center gap-2">
            <Phone className="w-6 h-6 text-primary" />
            Recent Calls
          </h2>

          {loading ? (
            <div className="space-y-4">
              {[1, 2, 3].map((i) => (
                <div
                  key={i}
                  className="flex items-center justify-between p-4 rounded-lg bg-muted/30"
                >
                  <div className="flex items-center gap-4 flex-1">
                    <div className="w-10 h-10 rounded-full bg-muted/50 animate-pulse" />
                    <div className="space-y-2">
                      <div className="h-4 w-32 bg-muted/50 rounded animate-pulse" />
                      <div className="h-3 w-20 bg-muted/50 rounded animate-pulse" />
                    </div>
                  </div>
                  <div className="flex items-center gap-6">
                    <div className="h-4 w-16 bg-muted/50 rounded animate-pulse" />
                    <div className="h-4 w-12 bg-muted/50 rounded animate-pulse" />
                    <div className="h-8 w-16 bg-muted/50 rounded animate-pulse" />
                  </div>
                </div>
              ))}
            </div>
          ) : recentCalls.length === 0 ? (
            <div className="text-center py-12">
              <Phone className="w-16 h-16 text-muted-foreground/50 mx-auto mb-4" />
              <p className="text-muted-foreground text-lg mb-2">
                No recent calls yet
              </p>
              <p className="text-muted-foreground/70 text-sm mb-6">
                Start your first call to see it appear here
              </p>
              <Link to="/live-call">
                <Button>
                  <Activity className="w-4 h-4 mr-2" />
                  Start Your First Call
                </Button>
              </Link>
            </div>
          ) : (
            <div className="space-y-4">
              {recentCalls.map((call, index) => (
                <div
                  key={call.id}
                  className="flex items-center justify-between p-4 rounded-lg bg-muted/30 hover:bg-muted/50 transition-all duration-300 border border-transparent hover:border-primary/20 animate-slide-in"
                  style={{ animationDelay: `${index * 100}ms` }}
                >
                  <div className="flex items-center gap-4 flex-1">
                    <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center">
                      <span className="text-primary font-semibold">
                        {getInitials(call.customerName)}
                      </span>
                    </div>
                    <div>
                      <p className="font-medium">{call.customerName}</p>
                      <p className={`text-sm ${emotionColor(call.sentiment)}`}>
                        {call.sentiment}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-6 text-sm text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <Activity className="w-4 h-4" />
                      {call.duration}
                    </span>
                    <div className="flex items-center gap-1">
                      <Star className="w-4 h-4 text-yellow-400 fill-yellow-400" />
                      {call.rating}
                    </div>
                    <Link to={`/summary/${call.id}`}>
                      <Button variant="ghost" size="sm">
                        View
                      </Button>
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      </main>
    </div>
  );
};

export default Dashboard;
