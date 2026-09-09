'use strict';
let csrf = '';
const byId = id => document.getElementById(id);
const field = (form, name) => form.elements.namedItem(name);
function say(text, error = false) { byId('message').textContent = text; byId('message').className = error ? 'error' : 'success'; }
function node(tag, text, className) { const element = document.createElement(tag); if (text !== undefined) element.textContent = text; if (className) element.className = className; return element; }
async function api(path, body) {
  const options = {credentials: 'same-origin', headers: {}};
  if (body !== undefined) { options.method = 'POST'; options.headers = {'Content-Type': 'application/json', 'X-CSRF-Token': csrf}; options.body = JSON.stringify(body); }
  const response = await fetch(path, options);
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || `请求失败 (${response.status})`);
  if (data.csrf_token) csrf = data.csrf_token;
  return data;
}
function action(label, callback, secondary = false) {
  const button = node('button', label, secondary ? 'secondary' : ''); button.type = 'button';
  button.addEventListener('click', async () => { button.disabled = true; try { await callback(); } catch (error) { say(error.message, true); } finally { button.disabled = false; } }); return button;
}
function renderEmpty(container, text) { if (!container.children.length) container.append(node('p', text, 'empty')); }
async function mediaFile(input) {
  const file = input.files[0]; if (!file) return undefined;
  if (file.size > 1024 * 1024) throw new Error('文件超过 1 MiB');
  return new Promise((resolve, reject) => { const reader = new FileReader(); reader.onerror = () => reject(new Error('读取文件失败')); reader.onload = () => resolve(String(reader.result).split(',')[1]); reader.readAsDataURL(file); });
}
function bind(formID, build, after) {
  const form = byId(formID);
  form.addEventListener('submit', async event => {
    event.preventDefault(); const submit = form.querySelector('button'); submit.disabled = true;
    try { const data = await api(form.getAttribute('action'), await build(form)); say('已保存'); if (after) await after(data, form); }
    catch (error) { say(error.message, true); } finally { submit.disabled = false; }
  });
}
async function loadMusic() {
  catalogs.music ||= createCatalog('music-catalog-form', 'music-list', 'music-pager', '/api/tracks', musicCard);
  return catalogs.music.load();
}
async function openAlbum(id) {
  const album = await api(`/api/albums/${encodeURIComponent(id)}`); byId('album-title').textContent = album.title;
  const container = byId('photo-list'); container.replaceChildren();
  for (const photo of album.photos) { const figure = node('figure', undefined, 'card'); const image = node('img'); image.src = photo.url; image.alt = photo.caption || '自产相片'; image.loading = 'lazy'; figure.append(image, node('figcaption', photo.caption)); container.append(figure); }
  renderEmpty(container, '相册里暂时还没有相片。');
}
async function loadAlbums() {
  catalogs.albums ||= createCatalog('albums-catalog-form', 'album-list', 'albums-pager', '/api/albums', albumCard);
  return catalogs.albums.load();
}
async function remove(kind, id) { if (!window.confirm('确认删除这条内容？')) return; await api('/api/admin/delete', {Kind: kind, ID: id}); await loadAdmin(); say('已删除'); }
function editForm(id, values) { const form = byId(id); for (const [name, value] of Object.entries(values)) { const input = field(form, name); if (input.type === 'checkbox') input.checked = value; else input.value = value; } form.scrollIntoView({behavior: 'smooth', block: 'center'}); }
async function loadAdmin() {
  const [site, users, content] = await Promise.all([api('/api/site'), api('/api/admin/users'), api('/api/admin/content')]);
  field(byId('site-form'), 'Title').value = site.title; field(byId('site-form'), 'Intro').value = site.intro;
  const userList = byId('user-list'); userList.replaceChildren();
  for (const user of users) { const row = node('article', undefined, 'row'); row.append(node('span', `${user.name || '未命名'} · ${user.email} · ${user.admin ? '管理员' : (user.enabled ? '已启用' : '已禁用')}`)); if (!user.admin) row.append(action(user.enabled ? '禁用' : '启用', async () => { await api('/api/admin/user-state', {ID: user.id, Enabled: !user.enabled}); await loadAdmin(); })); userList.append(row); }
  catalogs.adminTracks ||= createCatalog('admin-tracks-catalog-form', 'admin-tracks', 'admin-tracks-pager', '/api/admin/tracks', item => managementRow('tracks', item));
  catalogs.adminAlbums ||= createCatalog('admin-albums-catalog-form', 'admin-albums', 'admin-albums-pager', '/api/admin/albums', item => managementRow('albums', item));
  await Promise.all([catalogs.adminTracks.load(), catalogs.adminAlbums.load()]);
  const choices = byId('photo-album'); choices.replaceChildren();
  for (const album of content.albums) { const option = node('option', `${album.title} · ${publicationLabel(album.status)}`); option.value = album.id; choices.append(option); }
  const photos = byId('admin-photos'); photos.replaceChildren();
  for (const photo of content.photos) { const row = node('article', undefined, 'row'); row.append(node('span', `${photo.caption || '未命名相片'} · 相册 ${photo.album}`), action('删除相片', () => remove('photo', photo.id), true)); photos.append(row); }
}
async function start() {
  const page = document.body.dataset.page;
  for (const section of document.querySelectorAll('[data-section]')) section.hidden = section.dataset.section !== page;
  const session = await api('/api/session');
  byId('profile-link').hidden = !session.user; byId('logout').hidden = !session.user; byId('admin-link').hidden = !(session.user && session.user.admin);
  byId('logout').addEventListener('click', async () => { try { await api('/api/logout', {}); location.href = '/'; } catch (error) { say(error.message, true); } });
  const auth = form => ({Email: field(form, 'Email').value, Password: field(form, 'Password').value});
  bind('register-form', form => ({...auth(form), Name: field(form, 'Name').value}), () => { location.href = '/profile'; });
  bind('login-form', auth, () => { location.href = '/profile'; });
  bind('profile-form', form => ({Name: field(form, 'Name').value, Bio: field(form, 'Bio').value}));
  bind('site-form', form => ({Title: field(form, 'Title').value, Intro: field(form, 'Intro').value}), loadAdmin);
  bind('track-form', async form => ({ID: field(form, 'ID').value.trim(), Title: field(form, 'Title').value, Published: field(form, 'Published').checked, Audio: await mediaFile(field(form, 'Audio'))}), loadAdmin);
  bind('album-form', form => ({ID: field(form, 'ID').value.trim(), Title: field(form, 'Title').value, Description: field(form, 'Description').value, Published: field(form, 'Published').checked}), loadAdmin);
  bind('photo-form', async form => ({Album: field(form, 'Album').value, Caption: field(form, 'Caption').value, Data: await mediaFile(field(form, 'Data'))}), loadAdmin);
  if (page === 'music') await loadMusic();
  if (page === 'albums') await loadAlbums();
  if (page === 'profile') { const me = await api('/api/me'); byId('profile-email').textContent = me.email; field(byId('profile-form'), 'Name').value = me.name; field(byId('profile-form'), 'Bio').value = me.bio; }
  if (page === 'admin') await loadAdmin();
}
const catalogs = {};
const publicationLabel = status => ({draft: '草稿', published: '已发布', withdrawn: '已下架'}[status] || status);
function createCatalog(formID, listID, pagerID, collectionPath, render) {
  const form = byId(formID), list = byId(listID), pager = byId(pagerID);
  const endpoint = collectionPath.replace(/\/(tracks|albums)$/, '/catalog/$1');
  let page = 1, requestVersion = 0;
  const previous = node('button', '上一页'), status = node('span'), next = node('button', '下一页');
  previous.type = next.type = 'button'; previous.disabled = next.disabled = true;
  status.setAttribute('aria-live', 'polite'); pager.replaceChildren(previous, status, next);
  async function load() {
    const version = ++requestVersion;
    const params = new URLSearchParams({q: field(form, 'q').value.trim(), sort: field(form, 'sort').value, page: String(page), page_size: field(form, 'page_size').value});
    const state = field(form, 'state'); if (state) params.set('state', state.value);
    previous.disabled = next.disabled = true; status.textContent = '正在加载…';
    try {
      const result = await api(`${endpoint}?${params}`);
      if (version !== requestVersion) return;
      if (!Array.isArray(result.items) || !Number.isInteger(result.total) || result.total < 0) throw new Error('目录响应无效');
      const pages = Math.ceil(result.total / result.page_size);
      // A deletion or state change can remove the old last page.
      if (page > Math.max(1, pages)) { page = Math.max(1, pages); return load(); }
      list.replaceChildren(); for (const item of result.items) list.append(render(item));
      renderEmpty(list, '没有匹配的内容，请调整搜索或筛选。');
      status.textContent = `共 ${result.total} 条 · 第 ${page} / ${Math.max(1, pages)} 页`;
      previous.disabled = page <= 1; next.disabled = page >= pages;
    } catch (error) {
      if (version !== requestVersion) return;
      list.replaceChildren(); status.textContent = '加载失败，请重新搜索'; say(error.message, true);
    }
  }
  const reset = () => { page = 1; return load(); };
  form.addEventListener('submit', event => { event.preventDefault(); return reset(); });
  for (const name of ['sort', 'state', 'page_size']) { const input = field(form, name); if (input) input.addEventListener('change', reset); }
  previous.addEventListener('click', () => { if (!previous.disabled) { page--; return load(); } });
  next.addEventListener('click', () => { if (!next.disabled) { page++; return load(); } });
  return {load, reset};
}
function musicCard(track) {
  const card = node('article', undefined, 'card'); card.append(node('h2', track.title));
  const audio = node('audio'); audio.controls = true; audio.preload = 'none'; audio.src = track.url; card.append(audio); return card;
}
function albumCard(album) {
  const card = node('article', undefined, 'card'); card.append(node('h2', album.title), node('p', album.description), action('查看相册', () => openAlbum(album.id))); return card;
}
async function setPublication(kind, item, status) {
  const body = {ID: item.id, Title: item.title, Status: status};
  if (kind === 'albums') body.Description = item.description || '';
  await api(`/api/admin/${kind}`, body); await loadAdmin(); say(`已保存：${publicationLabel(status)}`);
}
function managementRow(kind, item) {
  const row = node('article', undefined, 'row'); row.append(node('span', `${item.title} · ${publicationLabel(item.status)}`));
  const album = kind === 'albums';
  const values = {ID: item.id, Title: item.title, Published: item.published}; if (album) values.Description = item.description || '';
  row.append(action('编辑', () => editForm(album ? 'album-form' : 'track-form', values)));
  for (const status of ['draft', 'published', 'withdrawn']) { if (status !== item.status) row.append(action(`设为${publicationLabel(status)}`, () => setPublication(kind, item, status), true)); }
  row.append(action('删除', () => remove(album ? 'album' : 'track', item.id), true)); return row;
}

if (typeof module !== 'undefined' && module.exports) module.exports = {createCatalog};
else start().catch(error => say(error.message, true));
