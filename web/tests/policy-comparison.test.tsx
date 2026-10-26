import React from 'react';
import {describe,it,expect,afterEach} from 'vitest';
import {render,screen,cleanup} from '@testing-library/react';
import PolicyComparison,{summarizePolicies} from '../app/policy-comparison';
afterEach(cleanup);
const policy=(holding:number,stockout:number,expedite:number)=>({annual_holding_cost:holding,expected_stockout_cost:stockout,expedite_spend:expedite});
describe('scenario annual cost comparison',()=>{
  it('reconciles multiple parts including cost increases',()=>{
    const parts=[{baseline:policy(10,20,5),optimized:policy(40,10,2)},{baseline:policy(1,2,3),optimized:policy(2,3,4)}];
    expect(summarizePolicies(parts)).toEqual({baseline:[11,22,8],optimized:[42,13,6]});
    render(<PolicyComparison parts={parts}/>);
    expect(screen.getByText(/Annual savings: -\$20.00/)).toBeTruthy();
    expect(screen.getByRole('img').getAttribute('aria-labelledby')).toBeTruthy();
    expect(screen.getByText('Total').parentElement?.textContent).toBe('Total$41.00$61.00$20.00');
  });
  it('does not turn missing or invalid costs into zero savings',()=>{
    expect(summarizePolicies([])).toBeNull();
    for(const invalid of [undefined,NaN,Infinity,-1,'12']){
      expect(summarizePolicies([{baseline:policy(1,2,3),optimized:{...policy(1,2,3),expedite_spend:invalid}}])).toBeNull();
    }
    render(<PolicyComparison parts={[{}]}/>);
    expect(screen.getByText('Cost breakdown unavailable for this scenario.')).toBeTruthy();
    expect(screen.queryByRole('img')).toBeNull();
  });
});
