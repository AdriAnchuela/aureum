export default function Panel({
  title,
  sub,
  children,
}: {
  title: string;
  sub?: string;
  children: React.ReactNode;
}) {
  return (
    <section className="card p-4">
      <header className="mb-3 flex items-baseline justify-between gap-2">
        <h2 className="text-sm font-semibold">{title}</h2>
        {sub && (
          <span className="text-[11px]" style={{ color: "var(--muted)" }}>
            {sub}
          </span>
        )}
      </header>
      {children}
    </section>
  );
}
