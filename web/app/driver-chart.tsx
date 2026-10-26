import {Bar,BarChart,CartesianGrid,ResponsiveContainer,Tooltip,XAxis,YAxis} from 'recharts';
export function driverPoints(value:unknown){
  if(!value||typeof value!=='object'||Array.isArray(value))return [];
  const entries=Object.entries(value);
  if(entries.some(([,v])=>typeof v!=='number'||!Number.isFinite(v)))return [];
  return entries.filter(([feature])=>feature!=='base_value').map(([feature,value])=>({feature,contribution:Number(value)})).sort((a,b)=>Math.abs(b.contribution)-Math.abs(a.contribution));
}
export default function DriverChart({explanation}:{explanation:Record<string,unknown>}){
  const points=driverPoints(explanation.contributions);
  if(!points.length)return <p>Model driver contributions unavailable.</p>;
  const base=(explanation.contributions as Record<string,number>).base_value;
  return <section aria-label="Model drivers"><h3>LightGBM driver contributions</h3>
    <p>TreeSHAP contributions in demand units for the fitted LightGBM model; this may differ from the selected forecast model. Contributions are associations, not causal effects.</p>
    <p>Base prediction: {Number.isFinite(base)?base.toFixed(3):'Unavailable'} units.</p>
    <div role="img" aria-label="Signed model driver contributions, sorted by absolute size; exact values below"><ResponsiveContainer width="100%" height={300}><BarChart data={points} layout="vertical" margin={{left:35}}><CartesianGrid strokeDasharray="3 3"/><XAxis type="number"/><YAxis type="category" dataKey="feature" width={100}/><Tooltip/><Bar dataKey="contribution" fill="#4197db" isAnimationActive={false}/></BarChart></ResponsiveContainer></div>
    <div className="table-wrap"><table><caption>Signed TreeSHAP contributions</caption><thead><tr><th scope="col">Feature</th><th scope="col">Contribution (units)</th></tr></thead><tbody>{points.map(p=><tr key={p.feature}><th scope="row">{p.feature}</th><td>{p.contribution.toFixed(4)}</td></tr>)}</tbody></table></div>
  </section>;
}
