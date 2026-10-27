import React from 'react';
import {it,expect,afterEach} from 'vitest';
import {render,screen,cleanup} from '@testing-library/react';
import NlpComparison from '../app/nlp-comparison';
afterEach(cleanup);
it('does not present missing or invalid metrics as measured accuracy',()=>{
  for(const value of [undefined,NaN,Infinity,-1,2,'1']) {
    render(<NlpComparison data={{status:'measured',baseline_macro_f1:value,zero_shot_macro_f1:1}}/>);
    expect(screen.queryByRole('table')).toBeNull();
    expect(screen.getByText(/not measured in the published results/)).toBeTruthy();
    cleanup();
  }
});
it('renders measured scores alongside sample limitations',()=>{
  render(<NlpComparison data={{status:'measured',baseline_macro_f1:2/3,zero_shot_macro_f1:1,test_rows:48,unique_heldout_templates:4,model:'test-flash',measured_at:'2026-10-27'}}/>);
  expect(screen.getByText('0.667')).toBeTruthy();
  expect(screen.getByText('1.000')).toBeTruthy();
  expect(screen.getByText(/48 synthetic rows from 4 held-out/)).toBeTruthy();
  expect(screen.getByText(/do not establish production accuracy/)).toBeTruthy();
});
