import {expect,test} from 'vitest';
import {histogramPoints,sensitivityPoints} from '../app/simulation-charts';
test('histogram preserves zero bins and draw totals',()=>{
 const points=histogramPoints({counts:[0,3,7],bins_usd:[0,10,20,30]});
 expect(points.map(p=>p.count)).toEqual([0,3,7]);
 expect(points.reduce((sum,p)=>sum+p.count,0)).toBe(10);
 expect(histogramPoints({counts:[2],bins_usd:[5,4]})).toEqual([]);
 expect(histogramPoints({counts:[2.5],bins_usd:[0,1]})).toEqual([]);
});
test('sensitivity sorts without mutating and rejects duplicate scenarios',()=>{
 const p={lead_time_multiplier:2,annual_cost:5,stock:3,fill_rate:0.99};
 const items=[p,{...p,lead_time_multiplier:0.5}];
 expect(sensitivityPoints(items)[0].lead_time_multiplier).toBe(0.5);
 expect(items[0]).toBe(p);
 expect(sensitivityPoints([p,p])).toEqual([]);
 expect(sensitivityPoints([{...p,fill_rate:2}])).toEqual([]);
});
