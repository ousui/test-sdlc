// Offline DOM-model regression consuming the real app.js and form fields.
// The hidden input's value/defaultValue reflection was separately reproduced in native Edge.
// This file does not certify native browser authentication or a complete client journey.
'use strict';
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.resolve(process.argv[2] || __dirname);
const html = fs.readFileSync(path.join(root, 'web/index.html'), 'utf8');
const source = fs.readFileSync(path.join(root, 'web/app.js'), 'utf8');
const attrs = raw => Object.fromEntries([...raw.matchAll(/([\w-]+)(?:="([^"]*)")?/g)].map(m => [m[1], m[2] || '']));
class Element {
  constructor() { this.listeners = {}; this.children = []; this.dataset = {}; this.hidden = false; }
  addEventListener(type, fn) { (this.listeners[type] ||= []).push(fn); }
  async fire(type) { const event = {preventDefault() {}}; for (const fn of this.listeners[type] || []) await fn(event); }
  append(...children) { this.children.push(...children); }
  replaceChildren(...children) { this.children = children; }
  scrollIntoView() {}
}
class Field extends Element {
  constructor(a) { super(); this.name=a.name || ''; this.type=a.type || 'text'; this.defaultValue=a.value || ''; this._value=this.defaultValue; this.checked=false; this.files=[]; }
  get value() { return this._value; }
  set value(value) { this._value=String(value); if(this.type==='hidden') this.defaultValue=this._value; }
  resetValue() { this._value=this.defaultValue; this.checked=false; this.files=[]; }
}
class Form extends Element {
  constructor(a, content) {
    super(); this.id=a.id; this.action=a.action; this.elements=[];
    for (const match of content.matchAll(/<(?:input|textarea|select)\b([^>]*)>/g)) this.elements.push(new Field(attrs(match[1])));
    this.elements.namedItem=name=>this.elements.find(field=>field.name===name) || null;
    this.submit = new Element(); this.resetButton = {click: () => this.reset()};
  }
  querySelector(selector) { return selector.includes('reset') ? this.resetButton : this.submit; }
  reset() {
    // Native form reset emits a cancelable event before applying default values.
    let canceled=false; const event={preventDefault(){canceled=true;}};
    for(const fn of this.listeners.reset || []) fn(event);
    if(!canceled) for(const field of this.elements) field.resetValue();
  }
}
const nodes={};
for(const match of html.matchAll(/\bid="([^"]+)"/g)) nodes[match[1]]=new Element();
for(const match of html.matchAll(/<form\b([^>]*)>([\s\S]*?)<\/form>/g)) { const a=attrs(match[1]); nodes[a.id]=new Form(a,match[2]); }
const posts=[];
const context=vm.createContext({console, Uint8Array, Promise, Object, String, Boolean, Error, JSON,
 btoa: s=>Buffer.from(s,'binary').toString('base64'),
 document:{getElementById:id=>nodes[id],createElement:()=>new Element(),querySelectorAll:()=>[],body:{dataset:{page:'home'}}},
 window:{confirm:()=>true,location:{assign(){}}},
 fetch:async (url,options)=>{const p=String(url); if(options.method==='POST') posts.push({path:p,body:JSON.parse(options.body)});
 const body=p==='/api/session'?{csrf_token:'review-token',user:null}:p==='/api/site'?{title:'Site',intro:'Intro'}:p==='/api/admin/content'?{tracks:[],albums:[],photos:[]}:['/api/admin/users','/api/tracks','/api/albums'].includes(p)?[]:{id:'saved'};
 return {ok:true,status:200,json:async()=>body};}
});
(async()=>{
 // Await the original boot and all original event handlers; do not substitute application functions.
 vm.runInContext(source.replace(/boot\(\)\.catch\(error => notice\(error\.message\)\);?\s*$/, 'globalThis.bootPromise = boot();'),context);
 await context.bootPromise;
 const results=[];
 for(const id of ['track-form','album-form']) {
   const form=nodes[id];
   vm.runInContext(`fill(byId(${JSON.stringify(id)}), {ID:'existing-content', Title:'Existing', Published:true})`,context);
   form.querySelector('button[type="reset"]').click();
   const afterNew=form.elements.namedItem('ID').value;
   vm.runInContext(`fill(byId(${JSON.stringify(id)}), {ID:'existing-content', Title:'Edited', Published:true})`,context);
   await form.fire('submit');
   const afterSave=form.elements.namedItem('ID').value;
   results.push({form:id,afterNew,afterSave,pass:afterNew==='' && afterSave===''});
 }
 console.log(JSON.stringify({kind:'DOM model using actual application source; no native authentication claim',results,posts},null,2));
 if(results.some(result=>!result.pass)) process.exitCode=1;
})().catch(error=>{console.error(error);process.exitCode=1;});
