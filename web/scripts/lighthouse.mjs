import lighthouse from 'lighthouse';
import {launch} from 'chrome-launcher';
import {readFileSync,writeFileSync} from 'node:fs';
const chrome=await launch({chromePath:process.env.CHROME_PATH,chromeFlags:['--headless','--no-sandbox','--disable-dev-shm-usage']});
try{
 const result=await lighthouse(process.env.TEST_BASE_URL||'http://host.docker.internal:3000',{port:chrome.port,output:'json',onlyCategories:['performance','accessibility','best-practices','seo']});
 const current=JSON.parse(readFileSync('../results/ui.json','utf8'));
 current.lighthouse={page:'Login',measured_at:new Date().toISOString(),scores:Object.fromEntries(Object.entries(result.lhr.categories).map(([key,value])=>[key,value.score])),environment:'local Docker Chrome'};
 writeFileSync('../results/ui.json',JSON.stringify(current,null,2));
 console.log(JSON.stringify(current.lighthouse));
}finally{await chrome.kill();}
