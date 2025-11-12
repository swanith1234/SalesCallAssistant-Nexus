import { NextResponse } from "next/server";
import clientPromise from "@/lib/db";
import bcrypt from "bcryptjs";

export async function POST(request: Request) {
  const { email, password } = await request.json();

  const client = await clientPromise;
  const db = client.db("sales-call-assistant"); // replace with your actual DB name
  const users = db.collection("users");

  // Check if user already exists
  const existing = await users.findOne({ email });
  if (existing) {
    return NextResponse.json({ message: "Email already registered" }, { status: 400 });
  }

  // Hash password
  const hashed = await bcrypt.hash(password, 10);

  // Insert user
  await users.insertOne({ email, password: hashed });

  return NextResponse.json({ message: "Account created" }, { status: 201 });
}
