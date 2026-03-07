
export default function Home() {

  const api = process.env.NEXT_PUBLIC_API_URL;

  return (
    <main className="flex min-h-screen items-center justify-center bg-black text-white">
      <div className="text-center space-y-4">
        <h1 className="text-4xl font-bold">Creative Storyteller</h1>

        <p className="text-gray-400">
          Backend API: {api}
        </p>
      </div>
    </main>
  );
}