// app/lib/supabase.ts
import { createClient } from "@supabase/supabase-js";

// In Vite/Remix, client-side environment variables need VITE_ prefix
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || "";
const supabaseKey = import.meta.env.VITE_SUPABASE_KEY || "";

if (!supabaseUrl || !supabaseKey) {
  console.warn(
    "Missing Supabase environment variables. Using placeholder values for development."
  );
  // For development, you can use placeholder values or handle this gracefully
}

export const supabase = createClient(
  supabaseUrl || "https://placeholder.supabase.co",
  supabaseKey || "placeholder-key"
);
