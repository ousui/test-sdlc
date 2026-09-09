'use strict';
const byId = id => document.getElementById(id);
let csrf = '';
let currentUser = null;
function notice(text) { byId('message').textContent = text; }
async function api(path, data) {
  const options = {credentials: 'same-origin'};
  if (data !== undefined) Object.assign(options, {method: 'POST', headers: {'Content-Type': 'application/json', 'X-CSRF-Token': csrf}, body: JSON.stringify(data)});
  const response = await fetch(path, options);
  const body = await response.json();
  if (body.csrf_token) csrf = body.csrf_token;
  if (!response.ok) throw new Error(body.error || `请求失败 (${response.status})`);
  return body;
}
function node(tag, text) { const element = document.createElement(tag); if (text !== undefined) element.textContent = text; return element; }
function button(text, callback) { const b = node('button', text); b.type = 'button'; b.addEventListener('click', () => Promise.resolve().then(callback).catch(error => notice(error.message))); return b; }
function fill(form, data) { for (const [key, value] of Object.entries(data)) { const field = form.elements.namedItem(key); if (field) { if (field.type === 'checkbox') field.checked = Boolean(value); else field.value = value ?? ''; } } }
async function encodeFile(file) {
  if (file.size > 1048576) throw new Error('媒体文件最多1MiB');
  const bytes = new Uint8Array(await file.arrayBuffer()); let binary = '';
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return btoa(binary);
}
async function formData(form) {
  const data = {};
  for (const field of form.elements) {
    if (!field.name) continue;
    if (field.type === 'file') { if (field.files.length) data[field.name] = await encodeFile(field.files[0]); }
    else data[field.name] = field.type === 'checkbox' ? field.checked : field.value;
  }
  return data;
}
function bind(id, onSuccess) {
  const form = byId(id);
  form.addEventListener('reset', () => {
    const identity = form.elements.namedItem('ID');
    if (identity) identity.value = '';
  });
  form.addEventListener('submit', async event => {
    event.preventDefault(); const submit = form.querySelector('button'); submit.disabled = true;
    try { const result = await api(form.action, await formData(form)); await onSuccess(result); notice('已保存'); }
    catch (error) { notice(error.message); }
    finally { submit.disabled = false; }
  });
}
const catalogControllers = new Map();
function createCatalog(formId, listId, pagerId, endpoint, render) {
  const form = byId(formId), list = byId(listId), pager = byId(pagerId);
  const field = name => form.elements.namedItem(name);
  let page = 1, generation = 0;
  const catalogEndpoint = endpoint.replace('/api/admin/', '/api/admin/catalog/').replace(/^\/api\/(?!admin\/)/, '/api/catalog/');
  function paging(total, size, failed = false) {
    const previous = button('上一页', async () => { page--; await load(); });
    const next = button('下一页', async () => { page++; await load(); });
    previous.disabled = failed || page <= 1;
    next.disabled = failed || page * size >= total;
    pager.replaceChildren(previous, node('span', failed ? '加载失败' : `第 ${page} 页 · 共 ${total} 条`), next);
  }
  async function load() {
    const ticket = ++generation;
    const size = Number(field('page_size').value || 10);
    const query = {q: field('q').value.trim(), sort: field('sort').value || 'title', page: String(page), page_size: String(size)};
    if (field('state')) query.state = field('state').value || 'all';
    const encoded = Object.entries(query).map(([key, value]) => encodeURIComponent(key) + '=' + encodeURIComponent(value)).join('&');
    try {
      const data = await api(catalogEndpoint + '?' + encoded);
      if (ticket !== generation) return;
      const lastPage = Math.max(1, Math.ceil(data.total / data.page_size));
      if (page > lastPage) { page = lastPage; return load(); }
      page = data.page;
      list.replaceChildren(...data.items.map(render));
      if (!data.items.length) list.append(node('p', '暂无符合条件的内容'));
      paging(data.total, data.page_size);
    } catch (error) {
      if (ticket !== generation) return;
      list.replaceChildren(); paging(0, size, true); notice(error.message);
    }
  }
  const reset = async event => { event.preventDefault(); page = 1; await load(); };
  form.addEventListener('submit', reset);
  for (const name of ['sort', 'page_size', 'state']) if (field(name)) field(name).addEventListener('change', reset);
  return {load};
}
function catalogOnce(prefix, list, endpoint, render) {
  if (!catalogControllers.has(prefix)) catalogControllers.set(prefix, createCatalog(prefix + '-catalog-form', list, prefix + '-pager', endpoint, render));
  return catalogControllers.get(prefix);
}
function trackRow(track) {
  const row = node('article'); row.append(node('h3', track.title));
  const audio = node('audio'); audio.controls = true; audio.preload = 'none'; audio.src = track.url; row.append(audio); return row;
}
function albumRow(album) {
  const row = node('article'); row.append(node('h3', album.title), node('p', album.description), button('查看相册', async () => {
    const detail = await api('/api/albums/' + encodeURIComponent(album.id)); const container = byId('album-detail'); container.replaceChildren(node('h3', detail.title));
    for (const photo of detail.photos) { const figure = node('figure'); const image = node('img'); image.src = photo.url; image.alt = photo.caption || '自产相册图片'; figure.append(image, node('figcaption', photo.caption)); container.append(figure); }
  })); return row;
}
async function loadPublic() {
  await Promise.all([catalogOnce('music', 'tracks', '/api/tracks', trackRow).load(), catalogOnce('albums', 'albums', '/api/albums', albumRow).load()]);
}
function managementRow(plural, singular, form, item) {
  const row = node('article'); row.append(node('span', `${item.title} · ${item.status}`), button('编辑', () => {
    fill(byId(form), {ID: item.id, Title: item.title, Description: item.description, Published: item.published}); byId(form).scrollIntoView();
  }), button('设为草稿', async () => {
    await api('/api/admin/' + plural, {ID: item.id, Title: item.title, ...(plural === 'albums' ? {Description: item.description} : {}), Status: 'draft'});
    await loadAdmin(); await loadPublic();
  }), button('删除', () => remove(singular, item.id))); return row;
}
async function remove(kind, id) { if (!window.confirm('确认删除这项内容？')) return; await api('/api/admin/delete', {Kind: kind, ID: id}); await loadAdmin(); await loadPublic(); }
async function loadAdmin() {
  const site = await api('/api/site'); fill(byId('site-form'), {Title: site.title, Intro: site.intro});
  const content = await api('/api/admin/content');
  await Promise.all([
    catalogOnce('admin-tracks', 'admin-tracks', '/api/admin/tracks', item => managementRow('tracks', 'track', 'track-form', item)).load(),
    catalogOnce('admin-albums', 'admin-albums', '/api/admin/albums', item => managementRow('albums', 'album', 'album-form', item)).load()
  ]);
  byId('photo-album').replaceChildren();
  for (const album of content.albums) { const option = node('option', album.title); option.value = album.id; byId('photo-album').append(option); }
  byId('admin-photos').replaceChildren();
  for (const photo of content.photos) { const row = node('article'); row.append(node('span', photo.caption || photo.id), button('删除照片', () => remove('photo', photo.id))); byId('admin-photos').append(row); }
  const users = await api('/api/admin/users'); byId('admin-users').replaceChildren();
  for (const user of users) { const row = node('article'); row.append(node('span', `${user.name} · ${user.email} · ${user.enabled ? '启用' : '停用'}`)); if (user.id !== currentUser.id) row.append(button(user.enabled ? '停用' : '启用', async () => { await api('/api/admin/user-state', {ID: user.id, Enabled: !user.enabled}); await loadAdmin(); })); byId('admin-users').append(row); }
}
async function boot() {
  for (const section of document.querySelectorAll('[data-section]')) section.hidden = section.dataset.section !== document.body.dataset.page;
  const session = await api('/api/session'); currentUser = session.user; byId('logout').hidden = !currentUser;
  byId('logout').addEventListener('click', async () => { try { await api('/api/logout', {}); window.location.assign('/'); } catch (error) { notice(error.message); } });
  bind('register-form', () => window.location.assign('/profile'));
  bind('login-form', () => window.location.assign('/profile'));
  bind('profile-form', () => {});
  bind('site-form', () => loadAdmin());
  bind('track-form', async () => { byId('track-form').reset(); await loadAdmin(); await loadPublic(); });
  bind('album-form', async () => { byId('album-form').reset(); await loadAdmin(); await loadPublic(); });
  bind('photo-form', async () => { byId('photo-form').reset(); await loadAdmin(); });
  if (document.body.dataset.page === 'music' || document.body.dataset.page === 'albums') await loadPublic();
  if (document.body.dataset.page === 'profile') { const me = await api('/api/me'); fill(byId('profile-form'), {Name: me.name, Bio: me.bio}); }
  if (document.body.dataset.page === 'admin') await loadAdmin();
}
if (typeof module !== 'undefined' && module.exports) module.exports = {createCatalog};
else boot().catch(error => notice(error.message));
