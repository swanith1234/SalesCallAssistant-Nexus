import { NextResponse } from "next/server";
import clientPromise from "@/lib/db";
import bcrypt from "bcryptjs";

export async function POST(request: Request) {
  const { email, password } = await request.json();

  const client = await clientPromise;
  const db = client.db("your_db_name"); // replace with your actual DB name
  const users = db.collection("users");

  // Find user
  const user = await users.findOne({ email });
  if (!user) {
    return NextResponse.json({ message: "Invalid credentials" }, { status: 401 });
  }

  // Check password
  const valid = await bcrypt.compare(password, user.password);
  if (!valid) {
    return NextResponse.json({ message: "Invalid credentials" }, { status: 401 });
  }

  // Auth success: You can return a token or session here if desired
  return NextResponse.json({ message: "Signin successful" });
}
