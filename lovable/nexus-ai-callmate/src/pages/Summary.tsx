import { useParams, Link } from "react-router-dom";
import { ArrowLeft, Download, ThumbsUp, ThumbsDown, Package, FileText } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import Navbar from "@/components/Navbar";

const Summary = () => {
  const { id } = useParams();

  const summaryData = {
    customer: "John Doe",
    date: "Jan 15, 2025",
    duration: "12:34",
    sentiment: "Happy",
    likes: [
      "Interested in automation features",
      "Appreciated the ROI analysis",
      "Liked the integration capabilities",
    ],
    doubts: [
      "Concerned about implementation timeline",
      "Questions about team training requirements",
    ],
    products: [
      { name: "Premium Plan", match: 85 },
      { name: "Enterprise Suite", match: 65 },
    ],
    feedback: "Strong interest shown. Follow up with detailed implementation plan and case studies.",
  };

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      
      <main className="container mx-auto px-4 pt-24 pb-12">
        <div className="mb-6">
          <Link to="/dashboard">
            <Button variant="ghost" className="gap-2 mb-4">
              <ArrowLeft className="w-4 h-4" />
              Back to Dashboard
            </Button>
          </Link>
          
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold mb-2 bg-gradient-primary bg-clip-text text-transparent">
                Call Summary
              </h1>
              <p className="text-muted-foreground">
                {summaryData.customer} • {summaryData.date} • {summaryData.duration}
              </p>
            </div>
            
            <Button variant="glass" className="gap-2">
              <Download className="w-4 h-4" />
              Export PDF
            </Button>
          </div>
        </div>

        <div className="grid lg:grid-cols-2 gap-6">
          {/* Customer Likes */}
          <Card className="p-6 bg-card/40 backdrop-blur-md border-primary/20 animate-slide-in">
            <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
              <ThumbsUp className="w-5 h-5 text-green-400" />
              What Customer Liked
            </h2>
            
            <ul className="space-y-3">
              {summaryData.likes.map((item, index) => (
                <li
                  key={index}
                  className="flex items-start gap-3 p-3 rounded-lg bg-green-500/10 border border-green-500/20"
                >
                  <div className="w-2 h-2 rounded-full bg-green-400 mt-2" />
                  <span className="text-sm flex-1">{item}</span>
                </li>
              ))}
            </ul>
          </Card>

          {/* Customer Doubts */}
          <Card className="p-6 bg-card/40 backdrop-blur-md border-primary/20 animate-slide-in" style={{ animationDelay: "100ms" }}>
            <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
              <ThumbsDown className="w-5 h-5 text-yellow-400" />
              Customer Concerns
            </h2>
            
            <ul className="space-y-3">
              {summaryData.doubts.map((item, index) => (
                <li
                  key={index}
                  className="flex items-start gap-3 p-3 rounded-lg bg-yellow-500/10 border border-yellow-500/20"
                >
                  <div className="w-2 h-2 rounded-full bg-yellow-400 mt-2" />
                  <span className="text-sm flex-1">{item}</span>
                </li>
              ))}
            </ul>
          </Card>

          {/* Recommended Products */}
          <Card className="p-6 bg-card/40 backdrop-blur-md border-primary/20 animate-slide-in" style={{ animationDelay: "200ms" }}>
            <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
              <Package className="w-5 h-5 text-primary" />
              Recommended Products
            </h2>
            
            <div className="space-y-4">
              {summaryData.products.map((product, index) => (
                <div
                  key={index}
                  className="p-4 rounded-lg bg-muted/30 border border-primary/10"
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium">{product.name}</span>
                    <Badge variant="outline" className="border-primary/40">
                      {product.match}% Match
                    </Badge>
                  </div>
                  <div className="h-2 bg-muted/50 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-primary rounded-full transition-all duration-500"
                      style={{ width: `${product.match}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </Card>

          {/* AI Feedback */}
          <Card className="p-6 bg-card/40 backdrop-blur-md border-primary/20 animate-slide-in" style={{ animationDelay: "300ms" }}>
            <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
              <FileText className="w-5 h-5 text-primary" />
              AI Feedback
            </h2>
            
            <div className="p-4 rounded-lg bg-primary/10 border border-primary/20">
              <p className="text-sm leading-relaxed">{summaryData.feedback}</p>
            </div>
            
            <div className="mt-4 pt-4 border-t border-border">
              <h3 className="text-sm font-medium mb-3">Next Steps</h3>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li className="flex items-center gap-2">
                  <div className="w-1.5 h-1.5 rounded-full bg-primary" />
                  Schedule follow-up call within 48 hours
                </li>
                <li className="flex items-center gap-2">
                  <div className="w-1.5 h-1.5 rounded-full bg-primary" />
                  Send detailed implementation timeline
                </li>
                <li className="flex items-center gap-2">
                  <div className="w-1.5 h-1.5 rounded-full bg-primary" />
                  Share relevant case studies
                </li>
              </ul>
            </div>
          </Card>
        </div>
      </main>
    </div>
  );
};

export default Summary;
