import {expect,test} from 'vitest';
import {answerText} from '../app/assistant-export';
test('exports answer provenance and citations without hidden session or tool data',()=>{
 const result=answerText({notice:'Mock routing',answer:'Savings: -20 [call-1]',session_id:'private-session'},[{tool:'get_kpis',tool_call_id:'call-1',data:{private:'not-for-export'}}]);
 expect(result).toContain('Mock routing');
 expect(result).toContain('Savings: -20 [call-1]');
 expect(result).toContain('get_kpis [call-1]');
 expect(result).not.toContain('private-session');
 expect(result).not.toContain('not-for-export');
});
