import { Phone, TrendingUp, Users, Star, Activity } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import Navbar from "@/components/Navbar";
import { Link } from "react-router-dom";

const Dashboard = () => {
  const recentCalls = [
    { id: 1, customer: "John Doe", emotion: "Happy", duration: "12:34", rating: 5 },
    { id: 2, customer: "Sarah Smith", emotion: "Confused", duration: "8:21", rating: 3 },
    { id: 3, customer: "Mike Johnson", emotion: "Neutral", duration: "15:42", rating: 4 },
    { id: 4, customer: "Emily Davis", emotion: "Upset", duration: "6:15", rating: 2 },
  ];

  const stats = [
    { label: "Total Calls", value: "124", icon: Phone, trend: "+12%" },
    { label: "Success Rate", value: "87%", icon: TrendingUp, trend: "+5%" },
    { label: "Active Users", value: "32", icon: Users, trend: "+8%" },
    { label: "Avg Rating", value: "4.2", icon: Star, trend: "+0.3" },
  ];

  const emotionColor = (emotion: string) => {
    const colors = {
      Happy: "text-green-400",
      Confused: "text-yellow-400",
      Neutral: "text-blue-400",
      Upset: "text-red-400",
    };
    return colors[emotion as keyof typeof colors] || "text-gray-400";
  };

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
          {stats.map((stat, index) => (
            <Card
              key={stat.label}
              className="p-6 bg-card/40 backdrop-blur-md border-primary/20 hover:border-primary/40 transition-all duration-300 hover:shadow-glow animate-slide-in"
              style={{ animationDelay: `${index * 100}ms` }}
            >
              <div className="flex items-start justify-between mb-4">
                <div className="p-3 rounded-lg bg-primary/10">
                  <stat.icon className="w-6 h-6 text-primary" />
                </div>
                <span className="text-sm text-green-400 font-medium">{stat.trend}</span>
              </div>
              <p className="text-3xl font-bold mb-1">{stat.value}</p>
              <p className="text-sm text-muted-foreground">{stat.label}</p>
            </Card>
          ))}
        </div>

        {/* Recent Calls */}
        <Card className="p-6 bg-card/40 backdrop-blur-md border-primary/20">
          <h2 className="text-2xl font-bold mb-6 flex items-center gap-2">
            <Phone className="w-6 h-6 text-primary" />
            Recent Calls
          </h2>
          
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
                      {call.customer.split(" ").map(n => n[0]).join("")}
                    </span>
                  </div>
                  <div>
                    <p className="font-medium">{call.customer}</p>
                    <p className={`text-sm ${emotionColor(call.emotion)}`}>
                      {call.emotion}
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
        </Card>
      </main>
    </div>
  );
};

export default Dashboard;
