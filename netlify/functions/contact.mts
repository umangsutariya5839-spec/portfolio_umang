import type { Config } from "@netlify/functions";
import { db } from "../../db/index.js";
import { contactMessages } from "../../db/schema.js";

const CORS_HEADERS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type",
  "Content-Type": "application/json",
};

export default async (req: Request) => {
  if (req.method === "OPTIONS") {
    return new Response(null, { status: 204, headers: CORS_HEADERS });
  }

  if (req.method !== "POST") {
    return new Response(JSON.stringify({ error: "Method not allowed" }), {
      status: 405,
      headers: CORS_HEADERS,
    });
  }

  let body: { name?: string; email?: string; subject?: string; message?: string };
  try {
    body = await req.json();
  } catch {
    return new Response(JSON.stringify({ error: "Invalid JSON body" }), {
      status: 400,
      headers: CORS_HEADERS,
    });
  }

  const { name, email, subject, message } = body;

  if (!name?.trim() || !email?.trim() || !subject?.trim() || !message?.trim()) {
    return new Response(JSON.stringify({ error: "All fields are required" }), {
      status: 400,
      headers: CORS_HEADERS,
    });
  }

  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(email)) {
    return new Response(JSON.stringify({ error: "Invalid email address" }), {
      status: 400,
      headers: CORS_HEADERS,
    });
  }

  try {
    const [inserted] = await db
      .insert(contactMessages)
      .values({
        name: name.trim(),
        email: email.trim().toLowerCase(),
        subject: subject.trim(),
        message: message.trim(),
      })
      .returning({ id: contactMessages.id });

    return new Response(
      JSON.stringify({ success: true, id: inserted.id, message: "Message received! I'll get back to you soon." }),
      { status: 201, headers: CORS_HEADERS }
    );
  } catch (err) {
    console.error("DB insert error:", err);
    return new Response(JSON.stringify({ error: "Failed to save message. Please try again." }), {
      status: 500,
      headers: CORS_HEADERS,
    });
  }
};

export const config: Config = {
  path: "/api/contact",
};
