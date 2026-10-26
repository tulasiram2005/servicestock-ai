import {useId} from 'react';

type Policy = Record<string, unknown>;
const fields = [
  ['annual_holding_cost', 'Holding'],
  ['expected_stockout_cost', 'Stockout'],
  ['expedite_spend', 'Expedite'],
] as const;
const usd = (value:number) => new Intl.NumberFormat('en-US',{style:'currency',currency:'USD'}).format(value);
const object = (value:unknown):Policy => value && typeof value==='object' ? value as Policy : {};

export function summarizePolicies(parts:Policy[]) {
  const totals = {baseline:[0,0,0],optimized:[0,0,0]};
  if(!parts.length)return null;
  for(const part of parts){
    for(const name of ['baseline','optimized'] as const){
      const policy=object(part[name]);
      for(let i=0;i<fields.length;i++){
        const value=policy[fields[i][0]];
        if(typeof value!=='number'||!Number.isFinite(value)||value<0)return null;
        totals[name][i]+=value;
      }
    }
  }
  return totals;
}

export default function PolicyComparison({parts}:{parts:Policy[]}){
  const titleId=useId();
  const totals=summarizePolicies(parts);
  if(!totals)return parts.length?<p>Cost breakdown unavailable for this scenario.</p>:null;
  const baseline=totals.baseline.reduce((a,b)=>a+b,0);
  const optimized=totals.optimized.reduce((a,b)=>a+b,0);
  let running=baseline;
  const changes=fields.map(([,label],i)=>{
    const delta=totals.optimized[i]-totals.baseline[i];
    const start=running;running+=delta;
    return {label,start,end:running,value:delta,total:false};
  });
  const bars=[{label:'Baseline',start:0,end:baseline,value:baseline,total:true},...changes,{label:'Optimized',start:0,end:optimized,value:optimized,total:true}];
  const low=Math.min(0,...bars.flatMap(bar=>[bar.start,bar.end]));
  const high=Math.max(1,...bars.flatMap(bar=>[bar.start,bar.end]));
  const y=(value:number)=>210-(value-low)/(high-low)*160;
  return <section aria-label="Scenario cost comparison">
    <h3>Baseline vs optimized annual cost</h3>
    <p>{parts.length} parts · Synthetic cost assumptions · USD per year</p>
    <p>Annual savings: {usd(baseline-optimized)}. Negative savings indicate a cost increase.</p>
    <div className="table-wrap"><table><caption>Annual cost breakdown (USD)</caption><thead><tr><th scope="col">Cost</th><th scope="col">Baseline</th><th scope="col">Optimized</th><th scope="col">Change</th></tr></thead><tbody>
      {fields.map(([,label],i)=><tr key={label}><th scope="row">{label}</th><td>{usd(totals.baseline[i])}</td><td>{usd(totals.optimized[i])}</td><td>{usd(totals.optimized[i]-totals.baseline[i])}</td></tr>)}
      <tr><th scope="row">Total</th><td>{usd(baseline)}</td><td>{usd(optimized)}</td><td>{usd(optimized-baseline)}</td></tr>
    </tbody></table></div>
    <svg viewBox="0 0 700 270" role="img" aria-labelledby={titleId} style={{width:'100%',maxWidth:900}}>
      <title id={titleId}>Annual cost waterfall: baseline {usd(baseline)}, optimized {usd(optimized)}. Component changes are listed in the table above.</title>
      <line x1="20" x2="680" y1={y(0)} y2={y(0)} stroke="currentColor"/>
      {bars.map((bar,i)=><g key={bar.label}>
        <rect x={30+i*135} y={Math.min(y(bar.start),y(bar.end))} width={95} height={Math.max(1,Math.abs(y(bar.end)-y(bar.start)))} fill={bar.total?'#4197db':bar.value>0?'#d88c28':'#799caa'}/>
        <text x={77+i*135} y={Math.min(y(bar.start),y(bar.end))-8} textAnchor="middle" fill="currentColor" fontSize={12}>{!bar.total&&bar.value>0?'+':''}{usd(bar.value)}</text>
        <text x={77+i*135} y={240} textAnchor="middle" fill="currentColor" fontSize={13}>{bar.label}</text>
      </g>)}
    </svg>
    <p>Each floating bar adds the optimized-minus-baseline change. Capital investment is excluded from annual operating cost.</p>
  </section>;
}
