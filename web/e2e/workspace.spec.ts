import {test,expect} from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import {readFileSync,writeFileSync,mkdirSync,existsSync} from 'node:fs';
import {resolve} from 'node:path';

const env=Object.fromEntries(readFileSync(resolve('../.env'),'utf8').trim().split('\n').map(line=>line.split('=')));
test('login, overview, part, scenario, assistant and configuration',async({page})=>{
  await page.goto('/');
  await expect(page.getByText('Synthetic cost assumptions',{exact:true})).toBeVisible();
  await page.getByLabel('Username',{exact:true}).fill('demo');
  await page.getByLabel('Password',{exact:true}).fill(env.DEMO_PASSWORD);
  await page.getByRole('button',{name:'Sign in',exact:true}).click();
  await expect(page.getByRole('heading',{name:'Overview',exact:true})).toBeVisible();
  const inventory=JSON.parse(readFileSync('../results/analytics.json','utf8')).kpis.inventory_value;
  await expect(page.getByText(new Intl.NumberFormat('en-US',{style:'currency',currency:'USD'}).format(inventory),{exact:true})).toBeVisible();
  await page.getByRole('button',{name:'Parts',exact:true}).click();
  await page.getByLabel('Search parts',{exact:true}).fill('P0001');
  await page.getByRole('button',{name:'Next page',exact:true}).click();
  await expect(page.getByRole('button',{name:'Open P0021',exact:true})).toBeVisible();
  await expect(page.getByLabel('Search parts',{exact:true})).toHaveValue('');
  await page.getByRole('combobox',{name:'ABC segment',exact:true}).selectOption('A');
  await page.getByRole('combobox',{name:'Part ID order',exact:true}).selectOption('desc');
  await page.getByRole('button',{name:'Search',exact:true}).click();
  await expect(page.getByText('Applied filters: A · Descending · All parts',{exact:true})).toBeVisible();
  await page.getByLabel('Saved view name',{exact:true}).fill('Priority parts');
  await page.getByRole('button',{name:'Save applied view',exact:true}).click();
  expect(await page.evaluate(()=>JSON.parse(localStorage.getItem('servicestock.part-views')||'[]'))).toEqual([
    {query:'',segment:'A',order:'desc',name:'Priority parts'}
  ]);
  await page.getByRole('button',{name:'Overview',exact:true}).click();
  await page.getByRole('button',{name:'Parts',exact:true}).click();
  await page.getByRole('button',{name:'Load Priority parts',exact:true}).click();
  await expect(page.getByRole('combobox',{name:'ABC segment',exact:true})).toHaveValue('A');
  await expect(page.getByRole('combobox',{name:'Part ID order',exact:true})).toHaveValue('desc');
  await page.getByRole('button',{name:'Delete Priority parts',exact:true}).click();
  await expect(page.getByRole('button',{name:'Load Priority parts',exact:true})).toHaveCount(0);
  await page.getByRole('combobox',{name:'ABC segment',exact:true}).selectOption('');
  await page.getByRole('combobox',{name:'Part ID order',exact:true}).selectOption('asc');
  await page.getByRole('button',{name:'Search',exact:true}).click();
  await page.getByRole('button',{name:'Open P0001',exact:true}).click();
  await expect(page.getByRole('heading',{name:'Part detail',exact:true})).toBeVisible();
  await page.getByRole('button',{name:'Policy Lab',exact:true}).click();
  await page.getByRole('button',{name:'Compare scenario',exact:true}).click();
  await expect(page.getByText(/Snapped to the nearest/)).toBeVisible();
  await page.getByRole('button',{name:'Assistant',exact:true}).click();
  await page.getByRole('button',{name:'Ask assistant',exact:true}).click();
  await expect(page.getByText(/Inventory value: USD/)).toBeVisible();
  await expect(page.locator('summary').filter({hasText:'get_kpis'})).toBeVisible();
  await page.getByRole('button',{name:'Configurations',exact:true}).click();
  await page.getByRole('button',{name:'Validate configuration',exact:true}).click();
  await expect(page.getByText('Configuration valid',{exact:true})).toBeVisible();
  await page.getByLabel('Sensor',{exact:true}).check();
  await page.getByRole('button',{name:'Compare option changes',exact:true}).click();
  await expect(page.getByText('Cost change: $59.00',{exact:true})).toBeVisible();
  const results=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa']).analyze();
  mkdirSync('../results',{recursive:true});
  const previous=existsSync('../results/ui.json')?JSON.parse(readFileSync('../results/ui.json','utf8')):{};
  writeFileSync('../results/ui.json',JSON.stringify({measured_at:new Date().toISOString(),page:'Configurations',axe_violations:results.violations.map(v=>({id:v.id,impact:v.impact,description:v.description})),lighthouse:previous.lighthouse||'not measured'},null,2));
  expect(results.violations).toEqual([]);
  await page.screenshot({path:'../results/workspace.png',fullPage:true});
});

test('administrator can inspect jobs and users',async({page})=>{
  await page.goto('/');
  await page.getByLabel('Username',{exact:true}).fill('admin');
  await page.getByLabel('Password',{exact:true}).fill(env.ADMIN_PASSWORD);
  await page.getByRole('button',{name:'Sign in',exact:true}).click();
  await page.getByRole('button',{name:'Admin',exact:true}).click();
  await page.getByRole('button',{name:'Refresh job monitor',exact:true}).click();
  await expect(page.getByRole('heading',{name:'Job monitor',exact:true})).toBeVisible();
  await expect(page.getByText('Latest 100 jobs. Refresh on demand to avoid idle database polling.')).toBeVisible();
  await page.getByRole('button',{name:'Users',exact:true}).click();
  await expect(page.getByRole('heading',{name:'Users and roles',exact:true})).toBeVisible();
  await expect(page.getByRole('cell',{name:'demo',exact:true})).toBeVisible();
  await expect(page.getByText('All current accounts are managed through environment configuration.')).toBeVisible();
});

test('user editing form submits role and disabled state (mocked user endpoints)',async({page})=>{
  let user={id:'ui-fixture',email:'fixture-user',role_id:'viewer',disabled:false,managed:false};
  await page.route('**/api/admin/users',route=>route.fulfill({json:[user]}));
  await page.route('**/api/admin/users/ui-fixture',async route=>{
    const body=route.request().postDataJSON();
    expect(body).toEqual({role:'planner',disabled:true});
    user={...user,role_id:body.role,disabled:body.disabled};
    await route.fulfill({json:{status:'updated'}});
  });
  await page.goto('/');
  await page.getByLabel('Username',{exact:true}).fill('admin');
  await page.getByLabel('Password',{exact:true}).fill(env.ADMIN_PASSWORD);
  await page.getByRole('button',{name:'Sign in',exact:true}).click();
  await page.getByRole('button',{name:'Admin',exact:true}).click();
  await page.getByRole('button',{name:'Users',exact:true}).click();
  await page.getByRole('combobox',{name:'Role for fixture-user'}).selectOption('planner');
  await page.getByLabel('Disable fixture-user',{exact:true}).check();
  await page.getByRole('button',{name:'Save access for fixture-user'}).click();
  await expect(page.getByText('Access updated.',{exact:true})).toBeVisible();
  await expect(page.getByRole('combobox',{name:'Role for fixture-user'})).toHaveValue('planner');
  await expect(page.getByLabel('Disable fixture-user',{exact:true})).toBeChecked();
});
