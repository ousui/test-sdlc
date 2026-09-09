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
  const container = byId('music-list'); container.replaceChildren();
  for (const track of await api('/api/tracks')) { const card = node('article', undefined, 'card'); card.append(node('h2', track.title)); const audio = node('audio'); audio.controls = true; audio.preload = 'none'; audio.src = track.url; card.append(audio); container.append(card); }
  renderEmpty(container, '还没有发布的试听，管理员可先上传自产测试音。');
}
async function openAlbum(id) {
  const album = await api(`/api/albums/${encodeURIComponent(id)}`); byId('album-title').textContent = album.title;
  const container = byId('photo-list'); container.replaceChildren();
  for (const photo of album.photos) { const figure = node('figure', undefined, 'card'); const image = node('img'); image.src = photo.url; image.alt = photo.caption || '自产相片'; image.loading = 'lazy'; figure.append(image, node('figcaption', photo.caption)); container.append(figure); }
  renderEmpty(container, '相册里暂时还没有相片。');
}
async function loadAlbums() {
  const container = byId('album-list'); container.replaceChildren();
  for (const album of await api('/api/albums')) { const card = node('article', undefined, 'card'); card.append(node('h2', album.title), node('p', album.description), action('查看相册', () => openAlbum(album.id))); container.append(card); }
  renderEmpty(container, '还没有发布的相册。');
}
async function remove(kind, id) { if (!window.confirm('确认删除这条内容？')) return; await api('/api/admin/delete', {Kind: kind, ID: id}); await loadAdmin(); say('已删除'); }
function editForm(id, values) { const form = byId(id); for (const [name, value] of Object.entries(values)) { const input = field(form, name); if (input.type === 'checkbox') input.checked = value; else input.value = value; } form.scrollIntoView({behavior: 'smooth', block: 'center'}); }
async function loadAdmin() {
  const [site, users, content] = await Promise.all([api('/api/site'), api('/api/admin/users'), api('/api/admin/content')]);
  field(byId('site-form'), 'Title').value = site.title; field(byId('site-form'), 'Intro').value = site.intro;
  const userList = byId('user-list'); userList.replaceChildren();
  for (const user of users) { const row = node('article', undefined, 'row'); row.append(node('span', `${user.name || '未命名'} · ${user.email} · ${user.admin ? '管理员' : (user.enabled ? '已启用' : '已禁用')}`)); if (!user.admin) row.append(action(user.enabled ? '禁用' : '启用', async () => { await api('/api/admin/user-state', {ID: user.id, Enabled: !user.enabled}); await loadAdmin(); })); userList.append(row); }
  const tracks = byId('admin-tracks'); tracks.replaceChildren();
  for (const track of content.tracks) { const row = node('article', undefined, 'row'); row.append(node('span', `${track.title} · ${track.published ? '已发布' : '草稿'}`), action('编辑', () => editForm('track-form', {ID: track.id, Title: track.title, Published: track.published})), action('删除', () => remove('track', track.id), true)); tracks.append(row); }
  const albums = byId('admin-albums'); albums.replaceChildren(); const choices = byId('photo-album'); choices.replaceChildren();
  for (const album of content.albums) { const option = node('option', album.title); option.value = album.id; choices.append(option); const row = node('article', undefined, 'row'); row.append(node('span', `${album.title} · ${album.published ? '已发布' : '草稿'}`), action('编辑', () => editForm('album-form', {ID: album.id, Title: album.title, Description: album.description, Published: album.published})), action('删除', () => remove('album', album.id), true)); albums.append(row); }
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
start().catch(error => say(error.message, true));
