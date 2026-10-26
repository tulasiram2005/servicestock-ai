export default function Home() {
  return <main>
    <header><a href="/" aria-label="ServiceStock AI home">S<span>ServiceStock AI</span></a><span className="badge">Local foundation</span></header>
    <section className="hero"><p className="eyebrow">YOUR OPERATIONS WORKSPACE</p><h1>A clearer view.<br/><span>Built from your data.</span></h1><p>One workspace for the service and stock workflows defined in your project specification.</p></section>
    <section className="cards" aria-label="Workspace status">
      <article><span className="number">01</span><h2>Data connection</h2><p>No data connected. Your workspace will show measured results when a data source is configured.</p><span className="state">Not connected</span></article>
      <article><span className="number">02</span><h2>Offline assistant</h2><p>The API includes a clearly labeled mock assistant. It operates without an AI account or external model calls.</p><span className="state">Mock mode</span></article>
      <article><span className="number">03</span><h2>Project setup</h2><p>The original project specification is needed to implement and verify the requested workflows.</p><span className="state">Specification pending</span></article>
    </section>
    <footer>Foundation preview · No customer records or measured performance results loaded.</footer>
  </main>;
}
