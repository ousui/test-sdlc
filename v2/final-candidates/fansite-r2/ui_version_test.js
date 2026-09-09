'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
class Element {
  constructor(tag='input', value='') { this.tagName=tag; this.value=value; this.type='text'; this.dataset={}; this.children=[]; this.listeners={}; this.disabled=false; this.textContent=''; }
  append(...xs) { this.children.push(...xs); }
  addEventListener(name,fn) { this.listeners[name]=fn; }
  scrollIntoView() {}
  setAttribute(k,v) { this[k]=v; }
}
const elements = {message:new Element('p')};
function form(kind) {
  const f=new Element('form');f.inputs={};for(const name of ['ID','Title','Intro','Description','Published','Version','Audio','Album','AlbumVersion'])f.inputs[name]=new Element('input');
  f.inputs.Published.type='checkbox';f.inputs.Audio.type='file';f.elements={namedItem:name=>f.inputs[name]||null};f.submit=new Element('button');f.querySelector=()=>f.submit;f.getAttribute=()=>`/api/admin/${kind==='track'?'tracks':kind==='album'?'albums':kind}`;elements[`${kind}-form`]=f;return f;
}
const site=form('site'),track=form('track'),album=form('album'),photo=form('photo');
global.document={getElementById:id=>elements[id],createElement:tag=>new Element(tag)};
global.window={confirm:()=>true};
const requests=[],responses=[];
global.fetch=async(path,options)=>{requests.push({path,options,body:options.body?JSON.parse(options.body):undefined});assert.equal(options.credentials,'same-origin');const r=responses.shift();assert.ok(r,'unexpected retry or GET');return {ok:r.status>=200&&r.status<300,status:r.status,json:async()=>r.data};};
const app=require('./web/app.js');
let checks=0;function equal(a,b){assert.deepEqual(a,b);checks++;}function ok(a){assert.ok(a);checks++;}
(async()=>{
 track.inputs.ID.value='track-id';track.inputs.Title.value='my unsaved input';track.dataset.version='3';
 let after=0;const build=f=>({ID:f.inputs.ID.value,Title:f.inputs.Title.value,Version:app.versionValue(f)});
 responses.push({status:409,data:{code:'version_conflict',error:'版本冲突'}});
 const count=requests.length;await app.saveForm(track,build,()=>after++);
 equal(requests.length,count+1);equal(requests.at(-1).body.Version,3);equal(track.inputs.Title.value,'my unsaved input');equal(track.dataset.version,'3');equal(track.dataset.conflict,'true');equal(track.submit.disabled,false);equal(after,0);ok(elements.message.textContent.includes('输入已保留'));ok(elements.message.textContent.includes('重新读取'));
 responses.push({status:200,data:{tracks:[{id:'track-id',title:'latest title',published:true,revision:4}],albums:[]}});
 await app.reloadEditor('track');equal(track.inputs.Title.value,'latest title');equal(track.dataset.version,'4');equal(track.dataset.conflict,'');equal(track.inputs.Audio.value,'');equal(requests.at(-1).path,'/api/admin/content');
 track.inputs.Title.value='chosen after reread';responses.push({status:200,data:{id:'track-id',revision:5}});await app.saveForm(track,build,()=>after++);
 equal(requests.at(-1).body,{ID:'track-id',Title:'chosen after reread',Version:4});equal(track.dataset.version,'5');equal(after,1);
 track.dataset.version='';responses.push({status:428,data:{code:'version_required',error:'缺少版本'}});await app.saveForm(track,build,()=>after++);
 equal(Object.hasOwn(requests.at(-1).body,'Version'),false);equal(track.inputs.Title.value,'chosen after reread');equal(after,1);equal(track.dataset.conflict,'true');
 site.inputs.Title.value='unsaved site';site.dataset.version='8';responses.push({status:500,data:{error:'storage failed'}});await app.saveForm(site,f=>({Title:f.inputs.Title.value,Version:app.versionValue(f)}));equal(site.inputs.Title.value,'unsaved site');equal(site.dataset.version,'8');
 responses.push({status:200,data:{title:'latest site',intro:'latest intro',revision:9}});await app.reloadEditor('site');equal(site.dataset.version,'9');equal(site.inputs.Intro.value,'latest intro');
 album.inputs.ID.value='deleted';album.inputs.Title.value='keep me';album.dataset.version='2';responses.push({status:200,data:{tracks:[],albums:[]}});await assert.rejects(()=>app.reloadEditor('album'),/已删除/);checks++;equal(album.inputs.Title.value,'keep me');equal(album.dataset.version,'2');
 responses.push({status:409,data:{error:'version conflict',code:'version_conflict'}});await assert.rejects(()=>app.setPublication('tracks',{id:'t',title:'old',revision:7},'withdrawn'));checks++;equal(requests.at(-1).body.Version,7);equal(requests.at(-1).body.Status,'withdrawn');
 responses.push({status:409,data:{error:'version conflict',code:'version_conflict'}});await assert.rejects(()=>app.remove('photo','p',6));checks++;equal(requests.at(-1).body,{Kind:'photo',ID:'p',Version:6});
 photo.dataset.albumVersion='11';equal(app.versionValue(photo,'AlbumVersion'),11);photo.dataset.albumVersion='';equal(app.versionValue(photo,'AlbumVersion'),undefined);
 responses.push({status:409,data:{error:'conflict',code:'version_conflict'}});try{await app.api('/api/admin/site',{Version:1});assert.fail('expected error')}catch(e){equal(e.status,409);equal(e.code,'version_conflict')}
 const html=fs.readFileSync('web/index.html','utf8'),source=fs.readFileSync('web/app.js','utf8');
 for(const name of ['site','track','album']){const body=html.match(new RegExp(`<form id="${name}-form"[\\s\\S]*?</form>`))[0];ok(!body.includes('name="Version"'));ok(body.includes(`id="${name}-reload"`));}
 ok(!html.includes('name="AlbumVersion"'));ok(html.includes('id="photo-reload"'));ok(source.includes("AlbumVersion: versionValue(form, 'AlbumVersion')"));ok(source.includes('Version: item.revision'));ok(source.includes('photo.revision'));equal(responses.length,0);
 console.log(`PASS: ${checks} version editor assertions; captured revisions, no retries, preserved conflict input, explicit reread, action versions and HTML bindings.`);
})().catch(e=>{console.error(e);process.exitCode=1;});
