export function answerText(answer:Record<string,unknown>,trace:Record<string,unknown>[]){
 const lines=['ServiceStock AI — assistant response',String(answer.notice||''),'',String(answer.answer||''),'','Source tool calls:'];
 for(const item of trace){
  lines.push(`${String(item.tool||'unknown')} [${String(item.tool_call_id||'unavailable')}]`);
 }
 lines.push('','Synthetic cost assumptions. This export contains the current answer and source references only.');
 return lines.join('\n');
}
