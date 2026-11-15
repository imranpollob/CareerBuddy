/** Render the original vector mark into browser/home-screen sizes.
 * Run after npm ci: node scripts/generate_brand_icons.mjs
 * Uses the existing local Chrome/Playwright tooling; no image service or network.
 */
import {readFile,writeFile} from 'node:fs/promises'
import {chromium} from '../frontend/node_modules/@playwright/test/index.mjs'
const publicDir=new URL('../frontend/public/',import.meta.url)
const svg=await readFile(new URL('brand/careerbuddy-mark.svg',publicDir),'utf8')
const browser=await chromium.launch({channel:'chrome',headless:true})
async function render(size,path,square=false){
 const page=await browser.newPage({viewport:{width:size,height:size},deviceScaleFactor:1})
 const mark=(square?svg.replace('rx="17"','rx="0"'):svg).replace('width="64" height="64"',`width="${size}" height="${size}"`)
 await page.setContent(`<html><head><style>html,body{margin:0;width:100%;height:100%;overflow:hidden;background:transparent}svg{display:block}</style></head><body>${mark}</body></html>`)
 const png=await page.screenshot({omitBackground:true})
 await writeFile(new URL(path,publicDir),png)
 await page.close()
 return png
}
try {
 const icons=[]
 for(const size of [16,32,48])icons.push({size,png:await render(size,`brand/favicon-${size}.png`)})
 await render(180,'apple-touch-icon.png',true)
 await render(192,'brand/icon-192.png')
 await render(512,'brand/icon-512.png')
 await render(512,'brand/icon-maskable-512.png',true)
 // ICO supports lossless PNG frames; keep a conventional multi-size fallback.
 const header=Buffer.alloc(6);header.writeUInt16LE(1,2);header.writeUInt16LE(icons.length,4)
 const entries=[];let offset=6+icons.length*16
 for(const {size,png} of icons){
  const entry=Buffer.alloc(16)
  entry[0]=size;entry[1]=size
  entry.writeUInt16LE(1,4);entry.writeUInt16LE(32,6)
  entry.writeUInt32LE(png.length,8);entry.writeUInt32LE(offset,12)
  entries.push(entry);offset+=png.length
 }
 await writeFile(new URL('favicon.ico',publicDir),Buffer.concat([header,...entries,...icons.map(i=>i.png)]))
 console.log('Exported CareerBuddy favicon, Apple touch icon, and app icons from the shared SVG.')
} finally {await browser.close()}
