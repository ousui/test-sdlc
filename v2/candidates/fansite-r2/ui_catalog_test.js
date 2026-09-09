'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
let checks = 0;
function check(value, message) { assert.ok(value, message); checks++; }
class Element {
  constructor(tag = 'div') { this.tag = tag; this.children = []; this.listeners = {}; this.value = ''; this.textContent = ''; this.disabled = false; }
  append(...children) { this.children.push(...children); }
  replaceChildren(...children) { this.children = children; }
  setAttribute(name, value) { this[name] = value; }
  addEventListener(name, listener) { (this.listeners[name] ||= []).push(listener); }
  async emit(name) { for (const listener of this.listeners[name] || []) await listener({preventDefault() {}}); }
}
const elements = new Map([['message', new Element()]]);
global.document = {getElementById: id => elements.get(id), createElement: tag => new Element(tag)};
const {createCatalog} = require('./web/app.js');
const requests = [];
const response = data => ({ok: true, json: async () => data});
let fetchImpl = async url => response({items: [{id: 'first', title: 'A'}], total: 21, page: Number(url.searchParams.get('page')), page_size: Number(url.searchParams.get('page_size'))});
global.fetch = (path, options) => { const url = new URL(path, 'http://fans.local'); requests.push(url); check(options.credentials === 'same-origin', 'lost authenticated fetch policy'); return fetchImpl(url); };
function fixture(prefix, admin = false) {
  const form = new Element('form'); const fields = {q: new Element('input'), sort: new Element('select'), page_size: new Element('select')};
  fields.sort.value = 'title'; fields.page_size.value = '10'; if (admin) { fields.state = new Element('select'); fields.state.value = 'all'; }
  form.elements = {namedItem: name => fields[name] || null}; const list = new Element(), pager = new Element();
  elements.set(prefix + '-form', form); elements.set(prefix + '-list', list); elements.set(prefix + '-pager', pager);
  const controller = createCatalog(prefix + '-form', prefix + '-list', prefix + '-pager', admin ? '/api/admin/tracks' : '/api/tracks', item => { const row = new Element(); row.textContent = item.title; return row; });
  return {form, fields, list, pager, controller};
}
async function main() {
  const f = fixture('test', true); await f.controller.load();
  check(requests.at(-1).pathname === '/api/admin/catalog/tracks', 'wrong catalog API');
  check(f.pager.children[0].disabled && !f.pager.children[2].disabled, 'first page boundaries');
  check(f.pager.children[1].textContent.includes('21'), 'filtered total not shown');
  await f.pager.children[2].emit('click'); check(requests.at(-1).searchParams.get('page') === '2', 'next page not requested');
  f.fields.q.value = '  Jazz  '; await f.form.emit('submit'); check(requests.at(-1).searchParams.get('q') === 'Jazz' && requests.at(-1).searchParams.get('page') === '1', 'search did not reset page');
  f.fields.sort.value = '-title'; await f.fields.sort.emit('change'); check(requests.at(-1).searchParams.get('sort') === '-title' && requests.at(-1).searchParams.get('page') === '1', 'sort reset');
  f.fields.state.value = 'withdrawn'; await f.fields.state.emit('change'); check(requests.at(-1).searchParams.get('state') === 'withdrawn', 'publication filter missing');
  const pending = [];
  fetchImpl = () => new Promise(resolve => pending.push(resolve));
  f.fields.q.value = 'old'; const old = f.controller.load(); f.fields.q.value = 'new'; const recent = f.controller.load();
  pending[1](response({items: [{id: 'new', title: 'New result'}], total: 1, page: 1, page_size: 10})); await recent;
  pending[0](response({items: [{id: 'old', title: 'Stale result'}], total: 99, page: 1, page_size: 10})); await old;
  check(f.list.children[0].textContent === 'New result' && f.pager.children[1].textContent.includes('共 1 条'), 'late response replaced current state');
  check(f.pager.children[0].disabled && f.pager.children[2].disabled, 'single page boundaries');
  fetchImpl = async () => ({ok: false, json: async () => ({error: 'Specific visible failure'})}); await f.controller.load();
  check(elements.get('message').textContent === 'Specific visible failure' && f.pager.children[1].textContent.includes('失败'), 'error hidden');
  let total = 11;
  fetchImpl = async url => response({items: [{id: 'x', title: 'One'}], total, page: Number(url.searchParams.get('page')), page_size: 10});
  const g = fixture('public'); await g.controller.load(); await g.pager.children[2].emit('click'); check(requests.at(-1).searchParams.get('page') === '2', 'second page');
  total = 10; await g.controller.load(); check(requests.at(-1).searchParams.get('page') === '1' && g.pager.children[0].disabled && g.pager.children[2].disabled, 'deleted final page not repaired');
  check(!requests.at(-1).searchParams.has('state'), 'public controller raised visibility');
  const html = fs.readFileSync('web/index.html', 'utf8');
  for (const id of ['music', 'albums', 'admin-tracks', 'admin-albums']) {
    const form = html.match(new RegExp(`<form id="${id}-catalog-form"[\\s\\S]*?</form>`)); check(form, 'missing actual page form ' + id);
    for (const name of ['q', 'sort', 'page_size']) check(form[0].includes(`name="${name}"`), 'missing bound control ' + name);
    check(html.includes(`id="${id}-pager"`), 'missing pager target');
    if (id.startsWith('admin')) check(form[0].includes('value="withdrawn"'), 'withdrawn state missing');
  }
  console.log(`PASS: ${checks} native catalog interaction/HTML assertions; search/sort/state reset, paging boundaries, stale-response isolation, error visibility and page removal.`);
}
main().catch(error => { console.error(error); process.exitCode = 1; });
