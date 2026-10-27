type Evidence = {[key: string]: unknown};
export default function NlpComparison({data}: {data: Evidence}) {
  const valid = (value: unknown): value is number => typeof value === 'number' && Number.isFinite(value) && value >= 0 && value <= 1;
  if(data.status !== 'measured' || !valid(data.baseline_macro_f1) || !valid(data.zero_shot_macro_f1))
    return <p>Zero-shot comparison not measured in the published results.</p>;
  return <section aria-label="Synthetic classifier comparison">
    <h3>Measured zero-shot comparison</h3>
    <p>{String(data.test_rows)} synthetic rows from {String(data.unique_heldout_templates)} held-out phrase templates. Repeated templates are not independent language examples; these scores do not establish production accuracy.</p>
    <table><caption>Macro-F1 · higher is better</caption><thead><tr><th>Classifier</th><th>Score</th></tr></thead>
      <tbody><tr><td>Offline TF-IDF baseline</td><td>{data.baseline_macro_f1.toFixed(3)}</td></tr>
        <tr><td>{String(data.model)} · zero-shot</td><td>{data.zero_shot_macro_f1.toFixed(3)}</td></tr></tbody></table>
    <p>Measured {String(data.measured_at)}. Risk flags continue to use the offline baseline.</p>
  </section>;
}
