import { useParams, Link } from "react-router-dom";
import { useEffect, useState } from "react";
import { ArrowLeft, Download } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import Navbar from "@/components/Navbar";

const Summary = () => {
  const { id } = useParams();
  const [data, setData] = useState(null);

  useEffect(() => {
    const fetchSummary = async () => {
      try {
        console.log("Fetching summary for ID:", id);
        const res = await fetch(`http://127.0.0.1:8000/call-summary/${id}`);
        const json = await res.json();
        setData(json);
      } catch (e) {
        console.error("Error fetching summary:", e);
      }
    };
    fetchSummary();
  }, [id]);

  if (!data) return <div className="text-center mt-20">Loading...</div>;

  return (
    <div className="min-h-screen bg-background">
      <Navbar />

      <main className="container mx-auto px-4 pt-24 pb-12">
        <Link to="/dashboard">
          <Button variant="ghost" className="gap-2 mb-4">
            <ArrowLeft className="w-4 h-4" /> Back to Dashboard
          </Button>
        </Link>

        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-4xl font-bold bg-gradient-primary bg-clip-text text-transparent">
              Call Summary
            </h1>

            <p className="text-muted-foreground">
              {data.userName} •{" "}
              {new Date(data.callDate).toLocaleString()} •{" "}
              {data.duration?.mmss}
            </p>
          </div>

          <Button className="gap-2" variant="glass">
            <Download className="w-4 h-4" /> Export PDF
          </Button>
        </div>

        <div className="grid lg:grid-cols-2 gap-6">

          <Card className="p-6 bg-card/40 border-primary/20">
            <h2 className="text-xl font-bold mb-4">Summary</h2>
            {data.summary}
          </Card>

          <Card className="p-6 bg-card/40 border-primary/20">
            <h2 className="text-xl font-bold mb-4">Call Purpose</h2>
            {data.callPurpose}
          </Card>

          <Card className="p-6 bg-card/40 border-primary/20">
            <h2 className="text-xl font-bold mb-4">User Experience</h2>
            {data.userExperience}
          </Card>

          <Card className="p-6 bg-card/40 border-primary/20">
            <h2 className="text-xl font-bold mb-4">Customer Phone</h2>
            {data.phoneNumber || "Not provided"}
          </Card>

        </div>
      </main>
    </div>
  );
};

export default Summary;
