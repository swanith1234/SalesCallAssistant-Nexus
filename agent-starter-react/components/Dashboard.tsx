'use client';

// for any hooks or client features
import Link from 'next/link';
import { Activity, Phone, Star, TrendingUp, Users } from 'lucide-react';
import Navbar from '@/components/ui/Navbar';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';

// Next.js routing

const Dashboard = () => {
  const recentCalls = [
    { id: 1, customer: 'John Doe', emotion: 'Happy', duration: '12:34', rating: 5 },
    { id: 2, customer: 'Sarah Smith', emotion: 'Confused', duration: '8:21', rating: 3 },
    { id: 3, customer: 'Mike Johnson', emotion: 'Neutral', duration: '15:42', rating: 4 },
    { id: 4, customer: 'Emily Davis', emotion: 'Upset', duration: '6:15', rating: 2 },
  ];

  const stats = [
    { label: 'Total Calls', value: '124', icon: Phone, trend: '+12%' },
    { label: 'Success Rate', value: '87%', icon: TrendingUp, trend: '+5%' },
    { label: 'Active Users', value: '32', icon: Users, trend: '+8%' },
    { label: 'Avg Rating', value: '4.2', icon: Star, trend: '+0.3' },
  ];

  const emotionColor = (emotion: string) => {
    const colors = {
      Happy: 'text-green-400',
      Confused: 'text-yellow-400',
      Neutral: 'text-blue-400',
      Upset: 'text-red-400',
    };
    return colors[emotion as keyof typeof colors] || 'text-gray-400';
  };

  return (
    <div className="bg-background min-h-screen">
      <Navbar />

      <main className="container mx-auto px-4 pt-24 pb-12">
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="bg-gradient-primary mb-2 bg-clip-text text-4xl font-bold text-transparent">
              Dashboard
            </h1>
            <p className="text-muted-foreground">
              Overview of your sales performance and recent calls
            </p>
          </div>
          <Link href="/">
            {' '}
            {/* Next.js styled linking */}
            <Button size="lg" className="gap-2">
              <Activity className="h-5 w-5" />
              Start Call
            </Button>
          </Link>
        </div>

        {/* Stats Grid */}
        <div className="mb-8 grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">
          {stats.map((stat, index) => (
            <Card
              key={stat.label}
              className="animate-slide-in border-primary/20 bg-card/40 shadow-elevation hover:border-primary/40 hover:shadow-glow p-6 backdrop-blur-md transition-all duration-300"
              style={{ animationDelay: `${index * 100}ms` }}
            >
              <div className="mb-4 flex items-start justify-between">
                <div className="bg-primary/10 rounded-lg p-3">
                  <stat.icon className="text-primary h-6 w-6" />
                </div>
                <span className="text-sm font-medium text-green-400">{stat.trend}</span>
              </div>
              <p className="mb-1 text-3xl font-bold">{stat.value}</p>
              <p className="text-muted-foreground text-sm">{stat.label}</p>
            </Card>
          ))}
        </div>

        {/* Recent Calls */}
        <Card className="bg-card/40 border-primary/20 p-6 backdrop-blur-md">
          <h2 className="mb-6 flex items-center gap-2 text-2xl font-bold">
            <Phone className="text-primary h-6 w-6" />
            Recent Calls
          </h2>

          <div className="space-y-4">
            {recentCalls.map((call, index) => (
              <div
                key={call.id}
                className="animate-slide-in bg-muted/30 hover:border-primary/20 hover:bg-muted/50 flex items-center justify-between rounded-lg border border-transparent p-4 transition-all duration-300"
                style={{ animationDelay: `${index * 100}ms` }}
              >
                <div className="flex flex-1 items-center gap-4">
                  <div className="bg-primary/20 flex h-10 w-10 items-center justify-center rounded-full">
                    <span className="text-primary font-semibold">
                      {call.customer
                        .split(' ')
                        .map((n) => n[0])
                        .join('')}
                    </span>
                  </div>
                  <div>
                    <p className="font-medium">{call.customer}</p>
                    <p className={`text-sm ${emotionColor(call.emotion)}`}>{call.emotion}</p>
                  </div>
                </div>

                <div className="text-muted-foreground flex items-center gap-6 text-sm">
                  <span className="flex items-center gap-1">
                    <Activity className="h-4 w-4" />
                    {call.duration}
                  </span>
                  <div className="flex items-center gap-1">
                    <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                    {call.rating}
                  </div>
                  <Link href={`/summary/${call.id}`}>
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
