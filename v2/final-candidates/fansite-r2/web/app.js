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
  if (!response.ok) { const error = new Error(body.error || `请求失败 (${response.status})`); error.status = response.status; error.code = body.code; throw error; }
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
    form.dataset.version = ''; form.dataset.conflict = '';
  });
  form.addEventListener('submit', async event => {
    event.preventDefault();
    if (['site-form', 'track-form', 'album-form', 'photo-form'].includes(id)) {
      return saveForm(form, async () => {
        const data = await formData(form);
        if (id === 'photo-form') return {...data, AlbumVersion: versionValue(form, 'AlbumVersion')};
        if (id === 'site-form' || data.ID) data.Version = versionValue(form);
        return data;
      }, onSuccess);
    }
    const submit = form.querySelector('button'); submit.disabled = true;
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
function versionValue(form, field = 'Version') {
  const value = form.dataset[field === 'AlbumVersion' ? 'albumVersion' : 'version'];
  if (!value) return undefined;
  const number = Number(value);
  return Number.isSafeInteger(number) && number > 0 ? number : undefined;
}
async function saveForm(form, build, after = async () => {}) {
  const submit = form.querySelector('button'); submit.disabled = true;
  try {
    const result = await api(form.action || form.getAttribute('action'), await build(form));
    if (result.revision !== undefined) form.dataset.version = String(result.revision);
    if (result.album_revision !== undefined) form.dataset.albumVersion = String(result.album_revision);
    form.dataset.conflict = ''; await after(result); notice('已保存'); return result;
  } catch (error) {
    if (error.status === 409 || error.status === 428) {
      form.dataset.conflict = 'true'; notice(error.message + '；输入已保留，请重新读取后决定如何保存。');
    } else notice(error.message + '；输入已保留。');
  } finally { submit.disabled = false; }
}
function fillEditor(kind, item) {
  const form = byId(kind + '-form');
  fill(form, kind === 'site' ? {Title: item.title, Intro: item.intro} : {ID: item.id, Title: item.title, Description: item.description, Published: item.published});
  const audio = form.elements.namedItem('Audio'); if (audio) audio.value = '';
  form.dataset.version = String(item.revision); form.dataset.conflict = ''; form.dataset.editorLoaded = 'true';
  return form;
}
async function reloadEditor(kind) {
  if (kind === 'site') return fillEditor(kind, await api('/api/site'));
  const form = byId(kind + '-form'), id = form.elements.namedItem('ID').value;
  const content = await api('/api/admin/content');
  const item = content[kind === 'track' ? 'tracks' : 'albums'].find(item => item.id === id);
  if (!item) throw new Error('内容已删除；输入已保留，请选择新建或其他内容。');
  return fillEditor(kind, item);
}
async function setPublication(plural, item, status) {
  return api('/api/admin/' + plural, {ID: item.id, Title: item.title, ...(plural === 'albums' ? {Description: item.description} : {}), Status: status, Version: item.revision});
}
function managementRow(plural, singular, form, item) {
  const row = node('article'); row.append(node('span', `${item.title} · ${item.status}`), button('编辑', () => {
    fillEditor(singular, item).scrollIntoView();
  }), button('设为草稿', async () => {
    await setPublication(plural, item, 'draft'); await loadAdmin(); await loadPublic();
  }), button('删除', () => remove(singular, item.id, item.revision))); return row;
}
async function remove(kind, id, revision) {
  if (!window.confirm('确认删除这项内容？')) return;
  await api('/api/admin/delete', {Kind: kind, ID: id, Version: revision}); await loadAdmin(); await loadPublic();
}
async function loadAdmin() {
  const site = await api('/api/site');
  if (!byId('site-form').dataset.editorLoaded) fillEditor('site', site);
  const content = await api('/api/admin/content');
  await Promise.all([
    catalogOnce('admin-tracks', 'admin-tracks', '/api/admin/tracks', item => managementRow('tracks', 'track', 'track-form', item)).load(),
    catalogOnce('admin-albums', 'admin-albums', '/api/admin/albums', item => managementRow('albums', 'album', 'album-form', item)).load()
  ]);
  const select = byId('photo-album'), form = byId('photo-form');
  const loaded = form.dataset.albumOptionsLoaded === 'true', selected = select.value;
  select.replaceChildren();
  for (const album of content.albums) { const option = node('option', album.title); option.value = album.id; select.append(option); }
  if (loaded) select.value = selected;
  const photoAlbumMissing = loaded && !content.albums.some(album => album.id === selected);
  if (photoAlbumMissing) select.value = '';
  const capture = () => {
    const chosen = content.albums.find(album => album.id === select.value);
    form.dataset.albumVersion = chosen ? String(chosen.revision) : '';
    form.dataset.conflict = '';
  };
  select.onchange = capture; capture(); form.dataset.albumOptionsLoaded = 'true';
  byId('admin-photos').replaceChildren();
  for (const photo of content.photos) { const row = node('article'); row.append(node('span', photo.caption || photo.id), button('删除照片', () => remove('photo', photo.id, photo.revision))); byId('admin-photos').append(row); }
  const users = await api('/api/admin/users'); byId('user-list').replaceChildren();
  for (const user of users) { const row = node('article'); row.append(node('span', `${user.name} · ${user.email} · ${user.enabled ? '启用' : '停用'}`)); if (user.id !== currentUser?.id) row.append(button(user.enabled ? '停用' : '启用', async () => { await api('/api/admin/user-state', {ID: user.id, Enabled: !user.enabled}); await loadAdmin(); })); byId('user-list').append(row); }
  return {photoAlbumMissing};
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
  for (const kind of ['site', 'track', 'album']) byId(kind + '-reload').addEventListener('click', () => reloadEditor(kind).then(() => notice('已重新读取，请确认后保存。')).catch(error => notice(error.message)));
  byId('photo-reload').addEventListener('click', () => loadAdmin().then(result => notice(result.photoAlbumMissing ? '原相册已删除；图片与说明已保留，请手动选择相册。' : '已重新读取相册版本；图片与说明已保留。')).catch(error => notice(error.message)));
  if (document.body.dataset.page === 'music' || document.body.dataset.page === 'albums') await loadPublic();
  if (document.body.dataset.page === 'profile') { const me = await api('/api/me'); fill(byId('profile-form'), {Name: me.name, Bio: me.bio}); }
  if (document.body.dataset.page === 'admin') await loadAdmin();
}
if (typeof module !== 'undefined' && module.exports) module.exports = {createCatalog, api, versionValue, saveForm, reloadEditor, setPublication, remove};
else boot().catch(error => notice(error.message));
