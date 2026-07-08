import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};

const files: Record<string, Record<string, string>> = {
  "wuxing-theory-book3": {
    docx: "wuxing-theory-book3/wuxing-theory-book3.docx",
    markdown: "wuxing-theory-book3/wuxing-theory-book3.md",
  },
};

function json(body: Record<string, unknown>, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...corsHeaders, "Content-Type": "application/json" },
  });
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }
  if (req.method !== "POST") {
    return json({ error: "Method not allowed" }, 405);
  }

  const supabaseUrl = Deno.env.get("SUPABASE_URL");
  const anonKey = Deno.env.get("SUPABASE_ANON_KEY");
  const serviceRoleKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  const bucket = Deno.env.get("PRIVATE_DOWNLOAD_BUCKET") || "private-downloads";

  if (!supabaseUrl || !anonKey || !serviceRoleKey) {
    return json({ error: "Download function is not configured" }, 500);
  }

  const authHeader = req.headers.get("Authorization") || "";
  if (!authHeader.startsWith("Bearer ")) {
    return json({ error: "Missing bearer token" }, 401);
  }

  const userClient = createClient(supabaseUrl, anonKey, {
    global: { headers: { Authorization: authHeader } },
  });
  const { data: userData, error: userError } = await userClient.auth.getUser();
  if (userError || !userData.user) {
    return json({ error: "Invalid session" }, 401);
  }

  let payload: { bookId?: string; format?: string };
  try {
    payload = await req.json();
  } catch {
    return json({ error: "Invalid JSON body" }, 400);
  }

  const bookId = payload.bookId || "wuxing-theory-book3";
  const format = payload.format || "docx";
  const path = files[bookId]?.[format];
  if (!path) {
    return json({ error: "Unknown book or format" }, 404);
  }

  const admin = createClient(supabaseUrl, serviceRoleKey);
  const { data, error } = await admin.storage.from(bucket).createSignedUrl(path, 300, {
    download: path.split("/").pop(),
  });
  if (error || !data?.signedUrl) {
    return json({ error: error?.message || "Unable to create signed URL" }, 500);
  }

  await admin.from("download_requests").insert({
    user_id: userData.user.id,
    book_id: bookId,
    format,
    client_info: {
      user_agent: req.headers.get("User-Agent") || "",
      referer: req.headers.get("Referer") || "",
    },
  });

  return json({
    signedUrl: data.signedUrl,
    expiresIn: 300,
    bookId,
    format,
  });
});
