import Link from "next/link";
export default function NotFound(){return <main className="grid min-h-screen place-items-center p-6 text-center"><div><p className="eyebrow">404 · Signal lost</p><h1 className="display mt-4">Off the map.</h1><p className="mt-5 text-muted">The route exists in neither language nor system.</p><Link className="mt-8 inline-block text-cyan" href="/en">Return home →</Link></div></main>}

