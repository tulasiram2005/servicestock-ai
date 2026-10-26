import {Area,ComposedChart,CartesianGrid,Line,ResponsiveContainer,Tooltip,XAxis,YAxis} from 'recharts';
type Forecast = {forecast?:unknown;intervals?:unknown};
export function forecastPoints(input:Forecast){
  const intervals=input.intervals as {lower?:unknown;upper?:unknown}|undefined;
  if(!Array.isArray(input.forecast)||!Array.isArray(intervals?.lower)||!Array.isArray(intervals?.upper))return [];
  const lower=intervals.lower,upper=intervals.upper;
  if(input.forecast.length!==lower.length||lower.length!==upper.length)return [];
  const points=input.forecast.map((value,index)=>({month:index+1,forecast:value,lower:lower[index],upper:upper[index],interval:[lower[index],upper[index]]}));
  if(points.some(p=>![p.forecast,p.lower,p.upper].every(v=>typeof v==='number'&&Number.isFinite(v)&&v>=0)||p.lower>p.upper))return [];
  return points;
}
export default function ForecastChart({data}:{data:Forecast}){
  const points=forecastPoints(data);
  if(!points.length)return <p>Forecast intervals unavailable.</p>;
  return <section aria-label="Forecast intervals"><h3>Demand forecast and prediction intervals</h3>
    <p>Months ahead · demand units. Shading shows the empirical prediction interval; coverage is not guaranteed.</p>
    <div role="img" aria-label="Forecast with lower and upper bounds; exact values in the following table">
      <ResponsiveContainer width="100%" height={280}><ComposedChart data={points}>
        <CartesianGrid strokeDasharray="3 3"/><XAxis dataKey="month"/><YAxis/><Tooltip/>
        <Area dataKey="interval" name="Prediction interval" stroke="#4197db" fill="#4197db" fillOpacity={0.2} isAnimationActive={false}/>
        <Line dataKey="forecast" name="Forecast" stroke="#d88c28" dot={false} isAnimationActive={false}/>
      </ComposedChart></ResponsiveContainer>
    </div>
    <div className="table-wrap"><table><caption>Forecast values in demand units</caption><thead><tr><th scope="col">Month ahead</th><th scope="col">Forecast</th><th scope="col">Lower bound</th><th scope="col">Upper bound</th></tr></thead><tbody>{points.map(p=><tr key={p.month}><th scope="row">{p.month}</th><td>{Number(p.forecast).toFixed(3)}</td><td>{Number(p.lower).toFixed(3)}</td><td>{Number(p.upper).toFixed(3)}</td></tr>)}</tbody></table></div>
  </section>;
}
