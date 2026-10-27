import {Bar,BarChart,CartesianGrid,Line,LineChart,ResponsiveContainer,Tooltip,XAxis,YAxis} from 'recharts';
export function histogramPoints(value:unknown){
 const h=value as {counts?:unknown;bins_usd?:unknown}|null;
 if(!h||!Array.isArray(h.counts)||!Array.isArray(h.bins_usd)||h.bins_usd.length!==h.counts.length+1)return [];
 const bins=h.bins_usd;
 if(h.counts.some(n=>!Number.isInteger(n)||n<0)||bins.some((n,i)=>typeof n!=='number'||!Number.isFinite(n)||(i>0&&n<=bins[i-1])))return [];
 return h.counts.map((count,i)=>({range:`${bins[i].toFixed(2)}–${bins[i+1].toFixed(2)}`,count}));
}
export function sensitivityPoints(value:unknown){
 if(!Array.isArray(value))return [];
 const valid=value.every(p=>p&&['lead_time_multiplier','annual_cost','stock','fill_rate'].every(k=>typeof p[k]==='number'&&Number.isFinite(p[k])&&p[k]>=0)&&p.lead_time_multiplier>0&&p.fill_rate<=1);
 if(!valid||new Set(value.map(p=>p.lead_time_multiplier)).size!==value.length)return [];
 return [...value].sort((a,b)=>a.lead_time_multiplier-b.lead_time_multiplier) as {lead_time_multiplier:number;annual_cost:number;stock:number;fill_rate:number}[];
}
export default function SimulationCharts({histogram,sensitivity}:{histogram:unknown;sensitivity:unknown}){
 const bins=histogramPoints(histogram),points=sensitivityPoints(sensitivity);
 return <>
 <section aria-label="Simulation histogram"><h3>Simulated remaining inventory value</h3><p>Synthetic assumptions · USD remaining after one lead-time cycle, not a time-series forecast. Bin counts are simulation draws.</p>
 {bins.length?<><ResponsiveContainer width="100%" height={260}><BarChart data={bins}><CartesianGrid strokeDasharray="3 3"/><XAxis dataKey="range" hide/><YAxis/><Tooltip/><Bar dataKey="count" name="Draws" fill="#4197db" isAnimationActive={false}/></BarChart></ResponsiveContainer><div className="table-wrap"><table><caption>Inventory simulation bins</caption><thead><tr><th scope="col">USD range</th><th scope="col">Draws</th></tr></thead><tbody>{bins.map((b,i)=><tr key={i}><th scope="row">{b.range}</th><td>{b.count}</td></tr>)}</tbody></table></div><p>Total draws: {bins.reduce((sum,b)=>sum+b.count,0)}. Intervals include the lower bound; only the final bin includes its upper bound.</p></>:<p>Simulation histogram unavailable.</p>}
 </section>
 <section aria-label="Lead-time sensitivity"><h3>Lead-time sensitivity</h3><p>Precomputed scenarios for this part at the displayed policy’s fixed service target and holding rate. Stock is reoptimized at each lead-time multiplier; lines connect sampled scenarios, not additional simulations.</p>
 {points.length?<><ResponsiveContainer width="100%" height={260}><LineChart data={points}><CartesianGrid strokeDasharray="3 3"/><XAxis dataKey="lead_time_multiplier" type="number" domain={['dataMin','dataMax']}/><YAxis/><Tooltip/><Line dataKey="annual_cost" name="Annual cost (USD)" stroke="#d88c28" isAnimationActive={false}/></LineChart></ResponsiveContainer><div className="table-wrap"><table><caption>Lead-time scenario values</caption><thead><tr><th scope="col">Lead multiplier</th><th scope="col">Annual cost (USD)</th><th scope="col">Stock (units)</th><th scope="col">Fill rate</th></tr></thead><tbody>{points.map(p=><tr key={p.lead_time_multiplier}><th scope="row">{p.lead_time_multiplier}</th><td>{p.annual_cost.toFixed(2)}</td><td>{p.stock}</td><td>{(p.fill_rate*100).toFixed(2)}%</td></tr>)}</tbody></table></div></>:<p>Lead-time scenarios unavailable.</p>}
 </section></>;
}
