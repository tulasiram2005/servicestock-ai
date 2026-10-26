import {expect,test} from 'vitest';
import {forecastPoints} from '../app/forecast-chart';
test('keeps forecast horizons and asymmetric bounds aligned',()=>{
 expect(forecastPoints({forecast:[1,3],intervals:{lower:[0,1],upper:[5,9]}})).toEqual([
  {month:1,forecast:1,lower:0,upper:5,interval:[0,5]},
  {month:2,forecast:3,lower:1,upper:9,interval:[1,9]},
 ]);
});
test('rejects incomplete, inverted and nonfinite intervals',()=>{
 for(const intervals of [{lower:[0],upper:[]},{lower:[4],upper:[2]},{lower:[0],upper:[NaN]},undefined]){
  expect(forecastPoints({forecast:[1],intervals})).toEqual([]);
 }
});
