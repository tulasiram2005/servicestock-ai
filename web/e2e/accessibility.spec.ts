import {test,expect} from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import {readFileSync,writeFileSync} from 'node:fs';
const env=Object.fromEntries(readFileSync('../.env','utf8').trim().split('\n').map(line=>line.split('=')));
test('all workspace pages pass automated WCAG checks in both themes',async({page})=>{
  test.setTimeout(120000);
  const checks:{page:string;theme:string;violations:unknown[]}[]=[];
  await page.goto('/');
  await page.getByLabel('Username',{exact:true}).fill('admin');
  await page.getByLabel('Password',{exact:true}).fill(env.ADMIN_PASSWORD);
  await page.getByRole('button',{name:'Sign in',exact:true}).click();
  await expect(page.getByRole('heading',{name:'Overview',exact:true})).toBeVisible();
  for(const theme of ['dark','light']){
    if(theme==='light') await page.getByRole('button',{name:'Toggle color theme'}).click();
    for(const name of ['Overview','Parts','Policy Lab','Data Quality','Assistant','Configurations','Results','Reports','Admin']){
      await page.getByRole('button',{name,exact:true}).click();
      await expect(page.getByRole('heading',{name,exact:true})).toBeVisible();
      await expect(page.getByText('Loading verified data…',{exact:true})).toHaveCount(0);
      const result=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze();
      checks.push({page:name,theme,violations:result.violations.map(v=>({id:v.id,impact:v.impact,nodes:v.nodes.map(n=>({target:n.target,summary:n.failureSummary}))}))});
    }
  }
  writeFileSync('../results/accessibility.json',JSON.stringify({measured_at:new Date().toISOString(),scope:'Automated axe checks on nine initial admin workspace views, two themes; not manual accessibility certification',checks},null,2));
  expect(checks.filter(row=>row.violations.length)).toEqual([]);
});

test('keyboard login and skip link bypass repeated workspace navigation',async({page})=>{
  await page.goto('/');
  await page.keyboard.press('Tab');
  await expect(page.getByRole('link',{name:'Skip to content'})).toBeFocused();
  await page.keyboard.press('Enter');
  await expect(page.locator('#workspace-content')).toBeFocused();
  await page.keyboard.press('Tab');
  await expect(page.getByLabel('Username',{exact:true})).toBeFocused();
  await page.keyboard.type('demo');
  await page.keyboard.press('Tab');
  await expect(page.getByLabel('Password',{exact:true})).toBeFocused();
  await page.keyboard.type(env.DEMO_PASSWORD);
  await page.keyboard.press('Tab');
  await expect(page.getByRole('button',{name:'Sign in',exact:true})).toBeFocused();
  await page.keyboard.press('Enter');
  await expect(page.getByRole('heading',{name:'Overview',exact:true})).toBeVisible();
  // Reach the first link with keyboard only after the login form is removed.
  for(let step=0;step<30;step++){
    await page.keyboard.press('Shift+Tab');
    if(await page.getByRole('link',{name:'Skip to content'}).evaluate(element=>element===document.activeElement)) break;
  }
  await expect(page.getByRole('link',{name:'Skip to content'})).toBeFocused();
  await page.keyboard.press('Enter');
  await expect(page.locator('#workspace-content')).toBeFocused();
});

test('workspace navigation and content fit tablet and mobile layouts',async({page})=>{
  await page.goto('/');
  await page.getByLabel('Username',{exact:true}).fill('demo');
  await page.getByLabel('Password',{exact:true}).fill(env.DEMO_PASSWORD);
  await page.getByRole('button',{name:'Sign in',exact:true}).click();
  await expect(page.getByRole('heading',{name:'Overview',exact:true})).toBeVisible();
  for(const width of [1024,768,390]){
    await page.setViewportSize({width,height:900});
    for(const name of ['Overview','Parts','Assistant']){
      await page.getByRole('button',{name,exact:true}).click();
      await expect(page.getByRole('heading',{name,exact:true})).toBeVisible();
      await expect(page.getByText('Loading verified data…',{exact:true})).toHaveCount(0);
      expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth+1)).toBe(true);
    }
  }
});
