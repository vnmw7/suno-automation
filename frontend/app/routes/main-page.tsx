import type { MetaFunction } from "@remix-run/node";
// import { createClient } from "@supabase/supabase-js";

// const supabaseUrl = process.env.SUPABASE_URL || "YOUR_SUPABASE_URL";
// const supabaseAnonKey =
//   process.env.SUPABASE_ANON_KEY || "YOUR_SUPABASE_ANON_KEY";

// const supabase = createClient(supabaseUrl, supabaseAnonKey);

export const meta: MetaFunction = () => {
  return [
    { title: "Main Page" },
    { name: "description", content: "This is the main page" },
  ];
};

// export async function loader() {
//   try {
//     const { data, error } = await supabase.from("your_table_name").select("*");

//     if (error) {
//       console.error("Supabase error:", error);
//       throw new Error(`Supabase error: ${error.message}`);
//     }

//     return { bibleData: data };
//   } catch (error) {
//     console.error("Error in loader:", error);
//     let errorMessage = "An unknown error occurred";
//     if (error instanceof Error) {
//       errorMessage = error.message;
//     }
//     return Response.json({ bibleData: null, error: errorMessage }, { status: 500 });
//   }
// }

export default function NextPage() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen">
      <h1>Welcome to the Next Page!</h1>
      <p>Suno automation dashboard will be displayed here.</p>
    </div>
  );
}
