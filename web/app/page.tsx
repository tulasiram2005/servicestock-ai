'use client';

import {FormEvent, useState} from 'react';
import PolicyComparison from './policy-comparison';
import ForecastChart from './forecast-chart';
import {Bar, BarChart, CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis} from 'recharts';

type Json = null | boolean | number | string | Json[] | {[key: string]: Json};
type RecordData = {[key: string]: Json};
type PartView = {query:string;segment:string;order:string};
type SavedView = PartView & {name:string};
const defaultPartView:PartView={query:'',segment:'',order:'asc'};
const pages = ['Overview', 'Parts', 'Policy Lab', 'Data Quality', 'Assistant', 'Configurations', 'Results', 'Reports', 'Admin'];
const money = (value: unknown) => typeof value === 'number' ? new Intl.NumberFormat('en-US', {style:'currency',currency:'USD'}).format(value) : 'Not measured';
const record = (value: Json | undefined): RecordData => value && typeof value === 'object' && !Array.isArray(value) ? value : {};
const rows = (value: Json | undefined): RecordData[] => Array.isArray(value) ? value.map(record) : [];

function Table({data}: {data: RecordData[]}) {
  if (!data.length) return <p className="empty">No records available.</p>;
  const keys = Object.keys(data[0]).filter(key => data.every(row => row[key] === null || typeof row[key] !== 'object'));
  return <div className="table-wrap"><table><thead><tr>{keys.map(key=><th key={key}>{key.replaceAll('_',' ')}</th>)}</tr></thead><tbody>{data.map((row,index)=><tr key={index}>{keys.map(key=><td key={key}>{typeof row[key] === 'number' ? Number(row[key]).toLocaleString('en-US',{maximumFractionDigits:3}) : String(row[key] ?? 'Not measured')}</td>)}</tr>)}</tbody></table></div>;
}

function Details({data}: {data: Json}) {
  return <details><summary>View source data</summary><pre>{JSON.stringify(data,null,2)}</pre></details>;
}

export default function Home() {
  const [token,setToken]=useState('');
  const [role,setRole]=useState('');
  const [page,setPage]=useState('Overview');
  const [data,setData]=useState<RecordData>({});
  const [busy,setBusy]=useState(false);
  const [notice,setNotice]=useState('');
  const [query,setQuery]=useState('');
  const [segment,setSegment]=useState('');
  const [order,setOrder]=useState('asc');
  const [appliedView,setAppliedView]=useState<PartView>(defaultPartView);
  const [savedViews,setSavedViews]=useState<SavedView[]>([]);
  const [viewName,setViewName]=useState('');
  const [part,setPart]=useState<RecordData|null>(null);
  const [answer,setAnswer]=useState<RecordData|null>(null);
  const [service,setService]=useState(0.95);
  const [holding,setHolding]=useState(0.2);
  const [lead,setLead]=useState(1);
  const [scenarioJob,setScenarioJob]=useState<RecordData|null>(null);
  const [scenarioResult,setScenarioResult]=useState<RecordData|null>(null);
  const [options,setOptions]=useState(['AC']);
  const [configuration,setConfiguration]=useState<RecordData|null>(null);
  const [comparisonOptions,setComparisonOptions]=useState(['AC']);
  const [configurationImpact,setConfigurationImpact]=useState<RecordData|null>(null);
  const [dark,setDark]=useState(true);
  const [toolTrace,setToolTrace]=useState<RecordData[]>([]);

  async function request(path:string, init:RequestInit={}, access=token):Promise<Json> {
    for(let attempt=0;attempt<4;attempt++){
      try {
        const response=await fetch('/api'+path,{...init,headers:{'Content-Type':'application/json',...(access?{Authorization:'Bearer '+access}:{}),...init.headers},signal:AbortSignal.timeout(20000)});
        if([502,503,504].includes(response.status)) throw new Error('wake');
        if(response.status===401){setToken('');throw new Error('Your session expired. Please sign in again.');}
        if(response.status===429) throw new Error('Request limit reached. Please wait a minute before retrying.');
        if(!response.ok){const body=await response.json().catch(()=>({}));throw new Error(typeof body.detail==='string'?body.detail:'This action is not available.');}
        return await response.json() as Json;
      }catch(error){
        const message=error instanceof Error?error.message:'Unable to connect';
        if(message!=='wake' && !(error instanceof TypeError) && !(error instanceof DOMException)) throw error;
        if(attempt===3) throw new Error('The server is unavailable. Please retry shortly.');
        setNotice('Waking up the server, this can take up to a minute');
        await new Promise(resolve=>setTimeout(resolve,1000*2**attempt));
      }
    }
    throw new Error('Please retry.');
  }
  async function action(work:()=>Promise<void>){
    setBusy(true);setNotice('');
    try{await work();}catch(error){setNotice(error instanceof Error?error.message:'Please retry.');}finally{setBusy(false);}
  }
  async function navigate(next:string,access=token){
    setPage(next);setPart(null);setData({});
    if(next==='Parts'){
      try{
        const stored:unknown=JSON.parse(localStorage.getItem('servicestock.part-views')||'[]');
        setSavedViews(Array.isArray(stored)?stored.filter((view):view is SavedView=>!!view&&typeof view==='object'&&typeof view.name==='string'&&view.name.length<=40&&typeof view.query==='string'&&view.query.length<=80&&['','A','B','C'].includes(view.segment)&&['asc','desc'].includes(view.order)).slice(0,5):[]);
      }catch{setSavedViews([]);}
      await loadParts(appliedView,'',access);return;
    }
    const endpoint:Record<string,string>={Overview:'/kpis',Parts:'/parts', 'Data Quality':'/dq',Configurations:'/configurations',Results:'/results',Admin:'/admin/usage'};
    if(endpoint[next]) setData(record(await request(endpoint[next],{},access)));
  }
  async function loadParts(view:PartView,cursor='',access=token){
    const params=new URLSearchParams({query:view.query,order:view.order,cursor});
    if(view.segment)params.set('segment',view.segment);
    const result=record(await request('/parts?'+params,{},access));
    setData(result);setAppliedView(view);setQuery(view.query);setSegment(view.segment);setOrder(view.order);
  }
  function saveViews(views:SavedView[]){
    try{localStorage.setItem('servicestock.part-views',JSON.stringify(views));setSavedViews(views);setNotice('Saved in this browser.');}
    catch{setNotice('Browser storage is unavailable. Filters still work without saving.');}
  }
  async function login(event:FormEvent<HTMLFormElement>){
    event.preventDefault();const form=new FormData(event.currentTarget);
    await action(async()=>{
      const result=record(await request('/auth/login',{method:'POST',body:JSON.stringify({username:form.get('username'),password:form.get('password')})},''));
      const access=String(result.access_token);setToken(access);setScenarioJob(null);setScenarioResult(null);
      const identity=record(await request('/me',{},access));setRole(String(identity.role));
      await navigate('Overview',access);
    });
  }
  async function submitScenario(){
    const body=JSON.stringify({service_level:service,holding_cost_rate:holding,lead_time_multiplier:lead,idempotency_key:Array.from(crypto.getRandomValues(new Uint8Array(16)),byte=>byte.toString(16).padStart(2,'0')).join('')});
    const submitted=record(await request('/whatif',{method:'POST',body}));
    setScenarioJob({id:submitted.job_id,status:submitted.status,progress:0});
    setScenarioResult(null);
  }
  async function refreshScenario(){
    if(!scenarioJob?.id)return;
    const updated=record(await request('/jobs/'+encodeURIComponent(String(scenarioJob.id))));
    setScenarioJob(updated);
    if(updated.status==='succeeded')setScenarioResult(record(updated.result));
  }
  async function logout(){
    const csrf=document.cookie.split('; ').find(value=>value.startsWith('csrf='))?.split('=')[1] || '';
    await action(async()=>{await request('/auth/logout',{method:'POST',headers:{'X-CSRF-Token':csrf}});setToken('');setData({});setAnswer(null);setScenarioJob(null);setScenarioResult(null);});
  }
  async function downloadReport(){
    await action(async()=>{
      const response=await fetch('/api/reports/review.pdf',{headers:{Authorization:'Bearer '+token}});
      if(!response.ok) throw new Error(response.status===403?'Planner or administrator access is required.':'Report is unavailable; please retry.');
      const url=URL.createObjectURL(await response.blob());
      const link=document.createElement('a');link.href=url;link.download='servicestock-review.pdf';link.click();
      setTimeout(()=>URL.revokeObjectURL(url),1000);
    });
  }
  async function ask(question:string){
    setAnswer(null);setToolTrace([]);
    const response=await fetch('/api/assistant/stream',{method:'POST',headers:{'Content-Type':'application/json',Authorization:'Bearer '+token},body:JSON.stringify({text:question}),signal:AbortSignal.timeout(30000)});
    if(!response.ok||!response.body) throw new Error(response.status===429?'Assistant request limit reached. Please retry later.':'Assistant unavailable. Please retry.');
    const reader=response.body.getReader();const decoder=new TextDecoder();let pending='';
    try {
      while(true){
        const next=await reader.read();if(next.done)break;
        pending+=decoder.decode(next.value,{stream:true});
        const events=pending.split('\n\n');pending=events.pop()||'';
        for(const event of events){
          const kind=event.split('\n').find(line=>line.startsWith('event: '))?.slice(7);
          const payload=event.split('\n').filter(line=>line.startsWith('data: ')).map(line=>line.slice(6)).join('\n');
          if(!payload)continue;
          const parsed=record(JSON.parse(payload) as Json);
          if(kind==='tool')setToolTrace(previous=>[...previous,parsed]);
          if(kind==='answer')setAnswer(parsed);
        }
      }
    }finally{reader.releaseLock();}
  }
  const kpis=record(data.kpis), finance=record(data.finance);
  return <main data-theme={dark?'dark':'light'}>
    <header><a href="/">S<span>ServiceStock AI</span></a><div className="badges"><span className="badge">Free-tier demo</span><span className="badge">Synthetic cost assumptions</span><button onClick={()=>setDark(!dark)} aria-label="Toggle color theme">{dark?'Light':'Dark'}</button>{token&&<button onClick={logout}>Sign out</button>}</div></header>
    <p className="provenance">Public car-parts demand · Synthetic costs, suppliers, lead times and comments · No SAP system was used.</p>
    <div role="status" aria-live="polite">{busy?<p className="loading">{notice||'Loading verified data…'}</p>:notice&&<p className="notice">{notice}</p>}</div>
    {!token?<section className="login"><p className="eyebrow">INVENTORY DECISION SUPPORT</p><h1>Stock with<br/><span>evidence.</span></h1><p>Explore demand, compare service policies, and understand the cost of your decisions.</p><form onSubmit={login}><label>Username<input name="username" autoComplete="username" required maxLength={64}/></label><label>Password<input name="password" type="password" autoComplete="current-password" required maxLength={256}/></label><button className="primary" disabled={busy}>Sign in</button></form><p>Local credentials are in your generated .env file. Demo access is read-only.</p></section>:<>
    <nav aria-label="Workspace">{pages.filter(item=>item!=='Admin'||role==='admin').map(item=><button key={item} aria-current={page===item?'page':undefined} onClick={()=>action(()=>navigate(item))}>{item}</button>)}</nav>
    <section><p className="eyebrow">WORKSPACE / {role}</p><h1 className="page-title">{part?'Part detail':page}</h1>
    {page==='Overview'&&<><div className="cards">{[['Inventory value',kpis.inventory_value],['Annual cost savings',kpis.annual_savings],['Working capital freed',kpis.working_capital_freed]].map(([label,value])=><article key={String(label)}><h2>{String(label)}</h2><strong>{money(value)}</strong></article>)}</div><p>Negative working capital freed means the recommendation requires more capital. These are simulated outcomes, not realized business savings.</p><h2>Service and risk</h2><Table data={[kpis]}/><h2>Monthly finance · USD</h2><Table data={rows(finance.monthly)}/><Details data={finance}/></>}
    {page==='Parts'&&!part&&<><form onSubmit={event=>{event.preventDefault();action(()=>loadParts({query,segment,order}));}} className="inline"><label>Search parts<input value={query} onChange={event=>setQuery(event.target.value)} maxLength={80}/></label><label>ABC segment<select value={segment} onChange={event=>setSegment(event.target.value)}><option value="">All segments</option>{['A','B','C'].map(value=><option key={value}>{value}</option>)}</select></label><label>Part ID order<select value={order} onChange={event=>setOrder(event.target.value)}><option value="asc">Ascending</option><option value="desc">Descending</option></select></label><button disabled={busy}>Search</button></form><p>Applied filters: {appliedView.segment||'All segments'} · {appliedView.order==='asc'?'Ascending':'Descending'} · {appliedView.query||'All parts'}</p><form className="inline" onSubmit={event=>{event.preventDefault();const name=viewName.trim();if(!name)return;saveViews([...savedViews.filter(view=>view.name!==name),{...appliedView,name}].slice(-5));setViewName('');}}><label>Saved view name<input value={viewName} onChange={event=>setViewName(event.target.value)} maxLength={40} required/></label><button disabled={busy}>Save applied view</button></form><p>Up to five views are saved in this browser, shared by its users. No credentials are saved.</p>{savedViews.map(view=><div className="inline" key={view.name}><button disabled={busy} onClick={()=>action(()=>loadParts(view))}>Load {view.name}</button><button disabled={busy} onClick={()=>saveViews(savedViews.filter(item=>item.name!==view.name))}>Delete {view.name}</button></div>)}<Table data={rows(data.items)}/><div className="part-links">{rows(data.items).map(item=><button key={String(item.id)} disabled={busy} onClick={()=>action(async()=>setPart(record(await request('/parts/'+item.id))))}>Open {String(item.id)}</button>)}</div>{data.next_cursor&&<button disabled={busy} onClick={()=>action(()=>loadParts(appliedView,String(data.next_cursor)))}>Next page</button>}</>}
    {part&&<><button onClick={()=>setPart(null)}>Back to parts</button><h2>{String(record(part.part).description)}</h2><Table data={[record(part.part)]}/><h2>Monthly demand · units</h2><div className="chart"><ResponsiveContainer width="100%" height={260}><LineChart data={rows(part.history)}><CartesianGrid strokeDasharray="3 3"/><XAxis dataKey="period"/><YAxis/><Tooltip/><Line dataKey="qty" stroke="#4197db" dot={false}/></LineChart></ResponsiveContainer></div><details><summary>Demand table</summary><Table data={rows(part.history)}/></details><h2>Policy comparison</h2><Table data={[{policy:'Baseline',...record(record(part.policy).baseline)},{policy:'Optimized',...record(record(part.policy).optimized)}]}/><h2>Forecast and drivers</h2><ForecastChart data={record(part.forecast)}/><Details data={part.forecast}/><Details data={part.policy}/></>}
    {page==='Policy Lab'&&<><p>Explore precomputed scenarios. Every request shows the nearest grid settings actually used.</p><form onSubmit={event=>{event.preventDefault();action(async()=>setData(record(await request('/whatif?service_level='+service+'&holding_cost_rate='+holding+'&lead_time_multiplier='+lead))));}}>{[['Service level',service,setService,0.8,0.999,0.001],['Holding cost rate',holding,setHolding,0.01,1,0.01],['Lead-time multiplier',lead,setLead,0.5,3,0.1]].map(([label,value,setter,min,max,step])=><label key={String(label)}>{String(label)}: {String(value)}<input type="range" value={Number(value)} min={Number(min)} max={Number(max)} step={Number(step)} onChange={event=>(setter as (value:number)=>void)(Number(event.target.value))}/></label>)}<button disabled={busy}>Compare scenario</button></form>{['admin','planner'].includes(role)&&<button disabled={busy} onClick={()=>action(submitScenario)}>Submit scenario job</button>}{scenarioJob&&<section aria-label="Scenario job"><h2>Scenario job</h2><p>Uses the precomputed grid. Refresh on demand; results belong to the submitted settings.</p><p role="status">Job status: {String(scenarioJob.status)}</p><progress aria-label="Scenario job progress" max={100} value={Number(scenarioJob.progress)||0}/><button disabled={busy} onClick={()=>action(refreshScenario)}>Refresh scenario job</button>{scenarioJob.error&&<p role="alert">{scenarioJob.status==='dead'?'Job failed after retries. Submit a new job to try again.':'The last attempt failed; the job is waiting to retry.'}</p>}{scenarioResult&&<><h3>Completed scenario</h3><p>{String(scenarioResult.notice||'')}</p><Table data={[record(scenarioResult.used)]}/><PolicyComparison parts={rows(scenarioResult.parts)}/><Table data={rows(scenarioResult.parts).map(item=>({part_id:item.part_id,annual_savings:item.annual_savings,working_capital_freed:item.working_capital_freed}))}/></>}</section>}{data.notice&&<p>{String(data.notice)}</p>}<Table data={data.used?[record(data.used)]:[]}/><PolicyComparison parts={rows(data.parts)}/><Table data={rows(data.parts).map(item=>({part_id:item.part_id,annual_savings:item.annual_savings,working_capital_freed:item.working_capital_freed}))}/></>}
    {page==='Data Quality'&&<><Table data={[data]}/><h2>Flagged and quarantined rows</h2><Table data={rows(data.issues)}/><Details data={data}/></>}
    {page==='Assistant'&&<><p>Offline, verified tool summaries. No external AI account is required.</p><form onSubmit={event=>{event.preventDefault();const form=new FormData(event.currentTarget);action(()=>ask(String(form.get('question'))));}}><label>Ask about KPIs, a part ID, or data quality<textarea name="question" maxLength={4000} required defaultValue="Show inventory KPIs"/></label><button disabled={busy}>Ask assistant</button></form><div aria-live="polite">{answer&&<article><p>{String(answer.notice)}</p><p>{String(answer.answer)}</p></article>}{toolTrace.map(trace=><details key={String(trace.tool_call_id)}><summary>{String(trace.tool)} · {String(trace.tool_call_id)}</summary><pre>{JSON.stringify(trace.data,null,2)}</pre></details>)}</div></>}
    {page==='Configurations'&&<><p>Select options to validate compatibility and calculate the component bill of materials.</p><form onSubmit={event=>{event.preventDefault();action(async()=>setConfiguration(record(await request('/configurations/evaluate',{method:'POST',body:JSON.stringify({model_id:'MODEL-1',options})}))));}}>{rows(data.options).map(option=><label className="checkbox" key={String(option.id)}><input type="checkbox" checked={options.includes(String(option.id))} onChange={event=>setOptions(event.target.checked?[...options,String(option.id)]:options.filter(item=>item!==option.id))}/>{String(option.name)}</label>)}<button disabled={busy}>Validate configuration</button></form>{configuration&&<><p>{configuration.valid?'Configuration valid':String(configuration.errors)}</p><Table data={rows(configuration.bom)}/><p>Total: {money(configuration.cost_usd)}</p></>}<h2>Commonality and pooling estimate</h2><p>{String(record(data.pooling).assumption||'')}</p><Table data={rows(record(data.pooling).parts)}/></>}
    {page==='Configurations'&&<><h2>Option change impact</h2><p>Compare current selections with: {comparisonOptions.join(', ')||'No options'}.</p><button disabled={busy} onClick={()=>action(async()=>{const result=record(await request('/configurations/evaluate',{method:'POST',body:JSON.stringify({model_id:'MODEL-1',options})}));if(!result.valid)throw new Error('Select a valid configuration before setting the comparison baseline.');setComparisonOptions([...options]);setConfigurationImpact(null);})}>Use selections as baseline</button><button disabled={busy} onClick={()=>action(async()=>setConfigurationImpact(record(await request('/configurations/impact',{method:'POST',body:JSON.stringify({model_id:'MODEL-1',before_options:comparisonOptions,options})}))))}>Compare option changes</button>{configurationImpact&&(configurationImpact.valid?<><p>Cost change: {money(configurationImpact.cost_change_usd)}</p><p>Lead-time change: {String(configurationImpact.lead_change_months)} months (parallel procurement).</p><Table data={rows(configurationImpact.component_changes)}/></>:<p>{String(configurationImpact.notice)}</p>)}</>}
    {page==='Results'&&<><p>Rendered from persisted run artifacts. Unmeasured fields remain explicitly unavailable.</p><h2>Forecast MAE · units</h2><div className="chart"><ResponsiveContainer width="100%" height={260}><BarChart data={Object.entries(record(record(data.benchmark).model_errors)).map(([model,value])=>({model,...record(value)}))}><CartesianGrid strokeDasharray="3 3"/><XAxis dataKey="model"/><YAxis/><Tooltip/><Bar dataKey="mae" fill="#4197db"/></BarChart></ResponsiveContainer></div><Table data={Object.entries(record(record(data.benchmark).model_errors)).map(([model,value])=>({model,...record(value)}))}/><h2>Lead-time regression</h2><Details data={record(data.analytics).regression}/><h2>Synthetic comment classification</h2><Details data={record(data.analytics).nlp}/></>}
    {page==='Reports'&&<><p>Review packs include verified run KPIs, recommendations, synthetic assumptions, methodology and limitations. Generated on demand without persistent report storage.</p>{role==='viewer'?<p>Read-only demo accounts cannot export. Sign in as a planner or administrator.</p>:<button disabled={busy} onClick={downloadReport}>Download PDF review pack</button>}</>}
    {page==='Admin'&&<><div className="inline"><button disabled={busy} onClick={()=>action(async()=>setData(record(await request('/admin/usage'))))}>Database usage</button><button disabled={busy} onClick={()=>action(async()=>setData({audit:await request('/admin/audit')}))}>Audit log</button><button disabled={busy} onClick={()=>action(async()=>setData({users:await request('/admin/users')}))}>Users</button><button disabled={busy} onClick={()=>action(async()=>setData({jobs:await request('/admin/jobs')}))}>Refresh job monitor</button></div><h2>{data.jobs?'Job monitor':data.audit?'Audit log':data.users?'Users and roles':'Measured database usage'}</h2>{data.jobs&&<p>Latest 100 jobs. Refresh on demand to avoid idle database polling.</p>}<Table data={data.jobs?rows(data.jobs):data.audit?rows(data.audit):data.users?rows(data.users):[data]}/><Details data={data}/></>}
    {page==='Admin'&&data.users&&<><h2>Edit access</h2><p>Environment-managed administrator and demo accounts are protected. Role changes invalidate existing access tokens.</p>{rows(data.users).filter(user=>!user.managed).map(user=><form key={String(user.id)+String(user.role_id)+String(user.disabled)} aria-label={'Edit '+user.email} onSubmit={event=>{event.preventDefault();const form=new FormData(event.currentTarget);action(async()=>{await request('/admin/users/'+encodeURIComponent(String(user.id)),{method:'POST',body:JSON.stringify({role:form.get('role'),disabled:form.get('disabled')==='on'})});setData({users:await request('/admin/users')});setNotice('Access updated.');});}}><h3>{String(user.email)}</h3><label>Role for {String(user.email)}<select name="role" defaultValue={String(user.role_id)}>{['viewer','planner','admin'].map(value=><option key={value}>{value}</option>)}</select></label><label className="checkbox"><input name="disabled" type="checkbox" defaultChecked={Boolean(user.disabled)}/>Disable {String(user.email)}</label><button disabled={busy}>Save access for {String(user.email)}</button></form>)}{rows(data.users).every(user=>user.managed)&&<p>All current accounts are managed through environment configuration.</p>}</>}
    {page==='Results'&&<><h2>Forecast interval validation</h2><p>Measured on six held-out monthly origins per part. Service hit rate measures demand within a forecast upper bound, not inventory fill rate. Empirical ranges have no guaranteed coverage.</p><Table data={rows(record(data.benchmark).parts).map(item=>({part_id:item.part_id,model:item.selected_model,...record(item.interval_backtest)}))}/></>}
    </section></>}
    <footer>ServiceStock AI · Scale-ready design; production capacity has not been proven.</footer>
  </main>;
}
