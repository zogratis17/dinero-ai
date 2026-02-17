// nextjs_api_route.ts
// Place this file in: app/api/generate/route.ts (App Router) 
// or pages/api/generate.ts (Pages Router)

import { NextResponse } from 'next/server';

// Configuration
const BACKEND_API_URL = process.env.LLM_BACKEND_URL || "https://your-tunnel-url.trycloudflare.com/generate";
const API_KEY = process.env.LLM_API_KEY || "prod_secret_key_123";

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { prompt } = body;

    if (!prompt) {
      return NextResponse.json({ error: "Prompt is required" }, { status: 400 });
    }

    // Forward the request to the Python FastAPI Backend
    // This keeps the backend URL hidden from the client browser
    const response = await fetch(BACKEND_API_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-api-key": API_KEY, // Authenticate with the backend
      },
      body: JSON.stringify({ prompt }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      return NextResponse.json(
        { error: `Backend Error: ${response.status}`, details: errorText }, 
        { status: response.status }
      );
    }

    const data = await response.json();
    
    // Return the data to the frontend
    return NextResponse.json(data);

  } catch (error) {
    console.error("API Route Error:", error);
    return NextResponse.json(
      { error: "Internal Server Error" }, 
      { status: 500 }
    );
  }
}
