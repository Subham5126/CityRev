// Follow this setup guide to integrate the Deno language server with your editor:
// https://deno.land/manual/getting_started/setup_your_environment
// This enables autocomplete, go to definition, etc.

// Setup type definitions for built-in Supabase Runtime APIs
// index.ts - Supabase Edge Function
import { serve } from "https://deno.land/std@0.177.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

// 🔹 Use environment variables (set inside Supabase project → Settings → Functions → Secrets)
const supabaseUrl = Deno.env.get("https://kxyejwmhqqqdkjwbxeiv.supabase.co") ?? "";
const supabaseKey = Deno.env.get("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imt4eWVqd21ocXFxZGtqd2J4ZWl2Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1ODA3ODcxMCwiZXhwIjoyMDczNjU0NzEwfQ.q059iunjpq0CpuMwY9eacPxh6bDrw1fB_uDOdpKxcUU") ?? ""; // service role key
const supabase = createClient(supabaseUrl, supabaseKey);

serve(async (req) => {
  // ✅ Handle CORS preflight request
  if (req.method === "OPTIONS") {
    return new Response("OK", {
      headers: {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
      },
    });
  }

  if (req.method !== "POST") {
    return new Response(JSON.stringify({ error: "Method Not Allowed" }), {
      status: 405,
      headers: { "Content-Type": "application/json" },
    });
  }

  try {
    const { image, report_id, description, category, location } = await req.json();

    if (!image || !report_id) {
      return new Response(JSON.stringify({ error: "Missing fields" }), {
        status: 400,
        headers: { "Content-Type": "application/json" },
      });
    }

    // 🔹 Convert base64 → Uint8Array
    const buffer = Uint8Array.from(atob(image), (c) => c.charCodeAt(0));

    // 🔹 Upload to Supabase Storage
    const fileName = `report-${report_id}.png`;
    const { error: storageError } = await supabase.storage
      .from("reports")
      .upload(fileName, buffer, {
        contentType: "image/png",
        upsert: true,
      });

    if (storageError) throw storageError;

    // 🔹 Get public URL
    const { data: publicUrlData } = supabase.storage
      .from("reports")
      .getPublicUrl(fileName);
    const publicUrl = publicUrlData.publicUrl;

    // 🔹 Insert into DB
    const { error: dbError } = await supabase.from("reports").insert([
      {
        report_id,
        description,
        category,
        location,
        image_url: publicUrl,
      },
    ]);

    if (dbError) throw dbError;

    // ✅ Success response
    return new Response(
      JSON.stringify({
        success: true,
        report_id,
        image_url: publicUrl,
      }),
      {
        headers: {
          "Content-Type": "application/json",
          "Access-Control-Allow-Origin": "*", // CORS
        },
      }
    );
  } catch (err) {
    return new Response(JSON.stringify({ success: false, error: err.message }), {
      status: 500,
      headers: {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*", // CORS
      },
    });
  }
});


/* To invoke locally:

  1. Run `supabase start` (see: https://supabase.com/docs/reference/cli/supabase-start)
  2. Make an HTTP request:

  curl -i --location --request POST 'http://127.0.0.1:54321/functions/v1/myFunction' \
    --header 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0' \
    --header 'Content-Type: application/json' \
    --data '{"name":"Functions"}'

*/
