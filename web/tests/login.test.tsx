import {render,screen,fireEvent,cleanup} from '@testing-library/react';
import {afterEach,expect,test,vi} from 'vitest';
import Home from '../app/page';
vi.mock('recharts',()=>({ResponsiveContainer:()=>null,Bar:()=>null,BarChart:()=>null,CartesianGrid:()=>null,Line:()=>null,LineChart:()=>null,Tooltip:()=>null,XAxis:()=>null,YAxis:()=>null}));
afterEach(cleanup);
test('shows provenance and requires credentials',()=>{
 render(<Home/>);
 expect(screen.getByText('Free-tier demo')).toBeTruthy();
 expect(screen.getByText('Synthetic cost assumptions')).toBeTruthy();
 expect((screen.getByLabelText('Password') as HTMLInputElement).type).toBe('password');
 expect((screen.getByLabelText('Username') as HTMLInputElement).required).toBe(true);
});
test('theme toggle is keyboard accessible',()=>{
 render(<Home/>);
 const button=screen.getByRole('button',{name:'Toggle color theme'});
 fireEvent.click(button);
 expect(button.textContent).toBe('Dark');
});
