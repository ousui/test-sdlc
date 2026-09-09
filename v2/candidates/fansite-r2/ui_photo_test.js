'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
// Narrow DOM model: rebuilding a non-multiple select selects its first option,
// matching the browser's ordinary select behavior. No native-browser claim.
class Element {
 constructor(tag='input', value='') { this.tagName=tag;this.value=value;this.type='text';this.dataset={};this.children=[];this.listeners={};this.disabled=false;this.textContent=''; }
 append(...children) { this.children.push(...children); }
 replaceChildren(...children) { this.children=[...children]; }
 addEventListener(name, fn) { this.listeners[name]=fn; }
 setAttribute(key,value) { this[key]=value; }
 scrollIntoView() {}
}
class Select extends Element {
 constructor() { super('select');this.selectedIndex=-1; }
 get value() { return this.children?.[this.selectedIndex]?.value || ''; }
 set value(value) { this.selectedIndex=this.children?.findIndex(x=>x.value===value) ?? -1; }
 get selectedOptions() { return this.selectedIndex<0?[]:[this.children[this.selectedIndex]]; }
 append(...children) { super.append(...children);if(this.selectedIndex<0&&this.children.length)this.selectedIndex=0; }
 replaceChildren(...children) { super.replaceChildren(...children);this.selectedIndex=children.length?0:-1; }
}
const elements={};
function form(id, names) { const f=new Element('form');f.inputs={};for(const [name,value] of Object.entries(names))f.inputs[name]=new Element('input',value);f.elements={namedItem:name=>f.inputs[name]||null};f.submit=new Element('button');f.querySelector=()=>f.submit;f.getAttribute=()=>'/api/admin/photos';elements[id]=f;return f; }
const photo=form('photo-form',{Caption:'my selected B photo',Data:'selected-image.png'});
const select=new Select();photo.inputs.Album=select;elements['photo-album']=select;
form('site-form',{Title:'',Intro:''});
for(const kind of ['tracks','albums'])form(`admin-${kind}-catalog-form`,{q:'',sort:'id_asc',page_size:'10',state:'all'});
for(const id of ['message','user-list','admin-tracks','admin-albums','admin-tracks-pager','admin-albums-pager','admin-photos'])elements[id]=new Element('div');
let latest=false,deleted=false;const writes=[];
const context=vm.createContext({module:{exports:{}},URLSearchParams,document:{getElementById:id=>elements[id],createElement:tag=>new Element(tag)},window:{confirm:()=>true},fetch:async(path,options)=>{
 let status=200,data;
 if(options.method==='POST'){const body=JSON.parse(options.body);writes.push(body);status=409;data={error:'版本冲突',code:'version_conflict'};}
 else if(path==='/api/site')data={title:'Site',intro:'Intro',revision:1};
 else if(path==='/api/admin/users')data=[];
 else if(path==='/api/admin/content')data={tracks:[],photos:[],albums:[{id:'a',title:'Alpha',status:'published',revision:12},{id:'b',title:'Beta',status:'published',revision:latest?8:7}]};
 else if(path.startsWith('/api/admin/catalog/'))data={items:[],total:0,page_size:10};
 else throw new Error(`unexpected request ${path}`);
 if (path === '/api/admin/content' && deleted) data.albums = data.albums.filter(album => album.id !== 'b');
 return{ok:status===200,status,json:async()=>data};
}});
vm.runInContext(fs.readFileSync(process.argv[2],'utf8'),context,{filename:'candidate/web/app.js'});
(async()=>{
 await vm.runInContext('loadAdmin()',context);
 select.value='b';select.onchange();assert.equal(select.value,'b');assert.equal(photo.dataset.albumVersion,'7');
 await context.module.exports.saveForm(photo,f=>({Album:f.inputs.Album.value,AlbumVersion:context.module.exports.versionValue(f,'AlbumVersion'),Caption:f.inputs.Caption.value,Data:f.inputs.Data.value}));
 assert.equal(writes.length,1);assert.equal(select.value,'b');assert.equal(photo.inputs.Caption.value,'my selected B photo');assert.equal(photo.inputs.Data.value,'selected-image.png');
 latest=true;
 // photo-reload's production handler calls loadAdmin(), then claims upload is preserved.
 await vm.runInContext('loadAdmin()',context);
 const observed={selectedAlbum:select.value,albumVersion:photo.dataset.albumVersion,caption:photo.inputs.Caption.value,file:photo.inputs.Data.value,writeRequests:writes};
 console.log(JSON.stringify(observed,null,2));
 assert.equal(select.value,'b','explicit photo reread must preserve the selected upload album B');
 assert.equal(photo.dataset.albumVersion,'8','reread should capture B current revision');
 deleted=true;
 const missing=await vm.runInContext('loadAdmin()',context);
 assert.equal(missing.photoAlbumMissing,true,'deleted selected album is reported');
 assert.equal(select.value,'','deleted B must never silently select A');
 assert.equal(photo.dataset.albumVersion,'','deleted target must not inherit another album version');
 assert.equal(photo.inputs.Caption.value,'my selected B photo');
 assert.equal(photo.inputs.Data.value,'selected-image.png');
 assert.equal(writes.length,1,'neither reread retries the POST');
 await vm.runInContext('loadAdmin()',context);
 console.log(JSON.stringify({afterSecondReread:select.value,albumVersion:photo.dataset.albumVersion,caption:photo.inputs.Caption.value}));
 assert.equal(select.value,'','repeated reread must not select a replacement album for a deleted target');
 assert.equal(photo.dataset.albumVersion,'');
 const stillMissing=await vm.runInContext('loadAdmin()',context);
 assert.equal(stillMissing.photoAlbumMissing,true);
 assert.equal(select.value,'','third reload must preserve the empty target');
 assert.equal(photo.dataset.albumVersion,'');
 select.value='a';select.onchange();
 await vm.runInContext('loadAdmin()',context);
 assert.equal(select.value,'a','explicit user choice becomes the preserved target');
 assert.equal(photo.dataset.albumVersion,'12');
 assert.equal(photo.inputs.Caption.value,'my selected B photo');
 assert.equal(photo.inputs.Data.value,'selected-image.png');
 assert.equal(writes.length,1,'all rereads remain read-only');
 console.log('PASS: selected album, input and current version preserved without retry');
})().catch(e=>{console.error(e);process.exitCode=1;});
