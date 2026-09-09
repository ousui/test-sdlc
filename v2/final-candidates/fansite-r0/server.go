package main

import (
	"bytes"
	"embed"
	"encoding/binary"
	"encoding/json"
	"errors"
	"html/template"
	"image"
	_ "image/jpeg"
	_ "image/png"
	"io"
	"mime"
	"net/http"
	"net/url"
	"sort"
	"strings"
	"sync"
	"time"
)

//go:embed web/*
var assets embed.FS

type session struct {
	UserID, CSRF string
	Version      uint64
	Expires      time.Time
}
type App struct {
	store    *Store
	secure   bool
	now      func() time.Time
	mu       sync.Mutex
	sessions map[string]session
}

func NewApp(s *Store, secure bool) *App {
	return &App{store: s, secure: secure, now: time.Now, sessions: map[string]session{}}
}
func (a *App) newSession(w http.ResponseWriter, r *http.Request, user string, version uint64) session {
	id := randomID()
	v := session{UserID: user, Version: version, CSRF: randomID(), Expires: a.now().Add(24 * time.Hour)}
	a.mu.Lock()
	if old, e := r.Cookie("fans_session"); e == nil {
		delete(a.sessions, old.Value)
	}
	a.sessions[id] = v
	a.mu.Unlock()
	http.SetCookie(w, &http.Cookie{Name: "fans_session", Value: id, Path: "/", HttpOnly: true, Secure: a.secure, SameSite: http.SameSiteStrictMode, MaxAge: 86400})
	return v
}
func (a *App) session(r *http.Request) (session, bool) {
	c, e := r.Cookie("fans_session")
	if e != nil {
		return session{}, false
	}
	a.mu.Lock()
	v, ok := a.sessions[c.Value]
	if ok && !a.now().Before(v.Expires) {
		delete(a.sessions, c.Value)
		ok = false
	}
	a.mu.Unlock()
	return v, ok
}
func (a *App) user(r *http.Request) (User, bool) {
	v, ok := a.session(r)
	if !ok || v.UserID == "" {
		return User{}, false
	}
	u, ok := a.store.Snapshot().Users[v.UserID]
	return u, ok && u.Enabled && u.SessionVersion == v.Version
}
func publicUser(u User) map[string]any {
	return map[string]any{"id": u.ID, "email": u.Email, "name": u.Name, "bio": u.Bio, "admin": u.Admin, "enabled": u.Enabled}
}
func respond(w http.ResponseWriter, status int, value any) {
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(value)
}
func problem(w http.ResponseWriter, err error) {
	code := 500
	switch {
	case errors.Is(err, errInvalid):
		code = 400
	case errors.Is(err, errMissing):
		code = 404
	case errors.Is(err, errForbidden):
		code = 403
	case errors.Is(err, errConflict):
		code = 409
	}
	message := "request failed"
	if code < 500 {
		message = err.Error()
	}
	respond(w, code, map[string]any{"error": message})
}
func readJSON(w http.ResponseWriter, r *http.Request, target any) bool {
	media, _, e := mime.ParseMediaType(r.Header.Get("Content-Type"))
	if e != nil || media != "application/json" {
		respond(w, 415, map[string]string{"error": "JSON required"})
		return false
	}
	dec := json.NewDecoder(http.MaxBytesReader(w, r.Body, 2<<20))
	dec.DisallowUnknownFields()
	if e = dec.Decode(target); e != nil {
		problem(w, errInvalid)
		return false
	}
	var tail any
	if dec.Decode(&tail) != io.EOF {
		problem(w, errInvalid)
		return false
	}
	return true
}
func (a *App) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("X-Content-Type-Options", "nosniff")
	w.Header().Set("Cache-Control", "no-store")
	w.Header().Set("Content-Security-Policy", "default-src 'self'; img-src 'self'; media-src 'self'; script-src 'self'; style-src 'self'; object-src 'none'; frame-ancestors 'none'")
	path := r.URL.Path
	if strings.HasPrefix(path, "/api/") {
		a.api(w, r)
		return
	}
	if strings.HasPrefix(path, "/media/") {
		a.media(w, r)
		return
	}
	if r.Method != "GET" && r.Method != "HEAD" {
		w.WriteHeader(405)
		return
	}
	if path == "/assets/app.js" || path == "/assets/style.css" {
		b, _ := assets.ReadFile("web/" + strings.TrimPrefix(path, "/assets/"))
		if strings.HasSuffix(path, ".js") {
			w.Header().Set("Content-Type", "text/javascript; charset=utf-8")
		} else {
			w.Header().Set("Content-Type", "text/css; charset=utf-8")
		}
		if r.Method == "GET" {
			w.Write(b)
		}
		return
	}
	page := map[string]string{"/": "home", "/music": "music", "/albums": "albums", "/login": "login", "/register": "register", "/profile": "profile", "/admin": "admin"}[path]
	if page == "" {
		http.NotFound(w, r)
		return
	}
	if page == "admin" || page == "profile" {
		u, ok := a.user(r)
		if !ok || (page == "admin" && !u.Admin) {
			http.Redirect(w, r, "/login", 303)
			return
		}
	}
	st := a.store.Snapshot()
	t, e := template.ParseFS(assets, "web/index.html")
	if e != nil {
		problem(w, e)
		return
	}
	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	if r.Method == "GET" {
		_ = t.Execute(w, map[string]string{"Title": st.Title, "Intro": st.Intro, "Page": page})
	}
}
func (a *App) api(w http.ResponseWriter, r *http.Request) {
	p := r.URL.Path
	get := r.Method == "GET"
	post := r.Method == "POST"
	allowedGet := p == "/api/session" || p == "/api/site" || p == "/api/me" || p == "/api/tracks" || p == "/api/albums" || strings.HasPrefix(p, "/api/albums/") || p == "/api/admin/users" || p == "/api/admin/content"
	allowedPost := p == "/api/register" || p == "/api/login" || p == "/api/logout" || p == "/api/me" || p == "/api/admin/site" || p == "/api/admin/user-state" || p == "/api/admin/tracks" || p == "/api/admin/albums" || p == "/api/admin/photos" || p == "/api/admin/delete"
	if !allowedGet && !allowedPost {
		http.NotFound(w, r)
		return
	}
	if !(get && allowedGet || post && allowedPost) {
		w.WriteHeader(405)
		return
	}
	u, authenticated := a.user(r)
	if p == "/api/me" && !authenticated || strings.HasPrefix(p, "/api/admin/") && (!authenticated || !u.Admin) {
		problem(w, errForbidden)
		return
	}
	if post {
		v, ok := a.session(r)
		if !ok || r.Header.Get("X-CSRF-Token") == "" || r.Header.Get("X-CSRF-Token") != v.CSRF {
			problem(w, errForbidden)
			return
		}
		if origin := r.Header.Get("Origin"); origin != "" {
			o, e := url.Parse(origin)
			scheme := "http"
			if r.TLS != nil {
				scheme = "https"
			}
			if e != nil || o.Scheme != scheme || o.Host != r.Host || o.Path != "" || o.RawQuery != "" || o.Fragment != "" {
				problem(w, errForbidden)
				return
			}
		}
	}
	if get {
		st := a.store.Snapshot()
		switch p {
		case "/api/session":
			v, ok := a.session(r)
			if !ok {
				v = a.newSession(w, r, "", 0)
			}
			var person any
			if authenticated {
				person = publicUser(u)
			}
			respond(w, 200, map[string]any{"csrf_token": v.CSRF, "user": person})
		case "/api/site":
			respond(w, 200, map[string]any{"title": st.Title, "intro": st.Intro})
		case "/api/me":
			respond(w, 200, publicUser(u))
		case "/api/tracks":
			respond(w, 200, tracksView(st, false))
		case "/api/albums":
			respond(w, 200, albumsView(st, false))
		case "/api/admin/content":
			respond(w, 200, map[string]any{"tracks": tracksView(st, true), "albums": albumsView(st, true), "photos": photosView(st, "")})
		case "/api/admin/users":
			users := []any{}
			for _, v := range st.Users {
				users = append(users, publicUser(v))
			}
			respond(w, 200, users)
		default:
			id := strings.TrimPrefix(p, "/api/albums/")
			al, ok := st.Albums[id]
			if !ok || !al.Published {
				problem(w, errMissing)
				return
			}
			respond(w, 200, map[string]any{"id": al.ID, "title": al.Title, "description": al.Description, "photos": photosView(st, id)})
		}
		return
	}
	switch p {
	case "/api/register":
		var in struct{ Email, Password, Name string }
		if !readJSON(w, r, &in) {
			return
		}
		person, e := a.store.Register(in.Email, in.Password, in.Name, false)
		if e != nil {
			problem(w, e)
			return
		}
		v := a.newSession(w, r, person.ID, person.SessionVersion)
		respond(w, 201, map[string]any{"user": publicUser(person), "csrf_token": v.CSRF})
	case "/api/login":
		var in struct{ Email, Password string }
		if !readJSON(w, r, &in) {
			return
		}
		email, e := cleanEmail(in.Email)
		if e != nil {
			problem(w, errForbidden)
			return
		}
		for _, person := range a.store.Snapshot().Users {
			if person.Email == email && person.Enabled && checkPassword(person, in.Password) {
				v := a.newSession(w, r, person.ID, person.SessionVersion)
				respond(w, 200, map[string]any{"user": publicUser(person), "csrf_token": v.CSRF})
				return
			}
		}
		problem(w, errForbidden)
	case "/api/logout":
		var in struct{}
		if !readJSON(w, r, &in) {
			return
		}
		a.mu.Lock()
		if c, e := r.Cookie("fans_session"); e == nil {
			delete(a.sessions, c.Value)
		}
		a.mu.Unlock()
		http.SetCookie(w, &http.Cookie{Name: "fans_session", Path: "/", MaxAge: -1, HttpOnly: true, Secure: a.secure, SameSite: http.SameSiteStrictMode})
		respond(w, 200, map[string]bool{"ok": true})
	case "/api/me":
		var in struct{ Name, Bio string }
		if !readJSON(w, r, &in) {
			return
		}
		in.Name = strings.TrimSpace(in.Name)
		if in.Name == "" || !validText(in.Name, 80) || !validText(in.Bio, 1000) {
			problem(w, errInvalid)
			return
		}
		e := a.store.Update(func(st *State) error {
			v := st.Users[u.ID]
			if !v.Enabled || v.SessionVersion != u.SessionVersion {
				return errForbidden
			}
			v.Name = in.Name
			v.Bio = in.Bio
			st.Users[u.ID] = v
			return nil
		})
		if e != nil {
			problem(w, e)
			return
		}
		respond(w, 200, publicUser(a.store.Snapshot().Users[u.ID]))
	case "/api/admin/site":
		var in struct{ Title, Intro string }
		if !readJSON(w, r, &in) {
			return
		}
		if strings.TrimSpace(in.Title) == "" || !validText(in.Title, 160) || !validText(in.Intro, 4000) {
			problem(w, errInvalid)
			return
		}
		e := a.store.Update(func(st *State) error { st.Title = in.Title; st.Intro = in.Intro; return nil })
		if e != nil {
			problem(w, e)
			return
		}
		respond(w, 200, map[string]bool{"ok": true})
	case "/api/admin/user-state":
		var in struct {
			ID      string
			Enabled bool
		}
		if !readJSON(w, r, &in) {
			return
		}
		if in.ID == u.ID && !in.Enabled {
			problem(w, errForbidden)
			return
		}
		e := a.store.Update(func(st *State) error {
			v, ok := st.Users[in.ID]
			if !ok {
				return errMissing
			}
			if v.Enabled != in.Enabled {
				v.SessionVersion++
			}
			v.Enabled = in.Enabled
			st.Users[in.ID] = v
			return nil
		})
		if e != nil {
			problem(w, e)
			return
		}
		respond(w, 200, map[string]bool{"ok": true})
	case "/api/admin/tracks":
		var in struct {
			ID, Title string
			Published bool
			Audio     []byte
		}
		if !readJSON(w, r, &in) {
			return
		}
		if strings.TrimSpace(in.Title) == "" || !validText(in.Title, 200) || in.Audio != nil && !validWAV(in.Audio) {
			problem(w, errInvalid)
			return
		}
		id := in.ID
		if id == "" {
			id = randomID()
		}
		e := a.store.Update(func(st *State) error {
			v, ok := st.Tracks[id]
			if in.ID != "" && !ok {
				return errMissing
			}
			if !ok && in.Audio == nil {
				return errInvalid
			}
			v.ID = id
			v.Title = in.Title
			v.Published = in.Published
			if in.Audio != nil {
				v.Audio = in.Audio
			}
			st.Tracks[id] = v
			return nil
		})
		if e != nil {
			problem(w, e)
			return
		}
		respond(w, 200, map[string]string{"id": id})
	case "/api/admin/albums":
		var in struct {
			ID, Title, Description string
			Published              bool
		}
		if !readJSON(w, r, &in) {
			return
		}
		if strings.TrimSpace(in.Title) == "" || !validText(in.Title, 200) || !validText(in.Description, 2000) {
			problem(w, errInvalid)
			return
		}
		id := in.ID
		if id == "" {
			id = randomID()
		}
		e := a.store.Update(func(st *State) error {
			if _, ok := st.Albums[id]; in.ID != "" && !ok {
				return errMissing
			}
			st.Albums[id] = Album{ID: id, Title: in.Title, Description: in.Description, Published: in.Published}
			return nil
		})
		if e != nil {
			problem(w, e)
			return
		}
		respond(w, 200, map[string]string{"id": id})
	case "/api/admin/photos":
		var in struct {
			Album, Caption string
			Data           []byte
		}
		if !readJSON(w, r, &in) {
			return
		}
		if !validImage(in.Data) || !validText(in.Caption, 500) {
			problem(w, errInvalid)
			return
		}
		id := randomID()
		e := a.store.Update(func(st *State) error {
			if _, ok := st.Albums[in.Album]; !ok {
				return errMissing
			}
			st.Photos[id] = Photo{ID: id, Album: in.Album, Caption: in.Caption, Data: in.Data}
			return nil
		})
		if e != nil {
			problem(w, e)
			return
		}
		respond(w, 200, map[string]string{"id": id})
	case "/api/admin/delete":
		var in struct{ Kind, ID string }
		if !readJSON(w, r, &in) {
			return
		}
		e := a.store.Update(func(st *State) error {
			switch in.Kind {
			case "track":
				if _, ok := st.Tracks[in.ID]; !ok {
					return errMissing
				}
				delete(st.Tracks, in.ID)
			case "album":
				if _, ok := st.Albums[in.ID]; !ok {
					return errMissing
				}
				delete(st.Albums, in.ID)
				for id, p := range st.Photos {
					if p.Album == in.ID {
						delete(st.Photos, id)
					}
				}
			case "photo":
				if _, ok := st.Photos[in.ID]; !ok {
					return errMissing
				}
				delete(st.Photos, in.ID)
			default:
				return errInvalid
			}
			return nil
		})
		if e != nil {
			problem(w, e)
			return
		}
		respond(w, 200, map[string]bool{"ok": true})
	}
}
func tracksView(st State, admin bool) []map[string]any {
	out := []map[string]any{}
	for _, v := range st.Tracks {
		if admin || v.Published {
			out = append(out, map[string]any{"id": v.ID, "title": v.Title, "published": v.Published, "url": "/media/tracks/" + v.ID})
		}
	}
	sort.Slice(out, func(i, j int) bool { return out[i]["id"].(string) < out[j]["id"].(string) })
	return out
}
func albumsView(st State, admin bool) []map[string]any {
	out := []map[string]any{}
	for _, v := range st.Albums {
		if admin || v.Published {
			out = append(out, map[string]any{"id": v.ID, "title": v.Title, "description": v.Description, "published": v.Published})
		}
	}
	sort.Slice(out, func(i, j int) bool { return out[i]["id"].(string) < out[j]["id"].(string) })
	return out
}
func photosView(st State, album string) []map[string]any {
	out := []map[string]any{}
	for _, v := range st.Photos {
		if album == "" || v.Album == album {
			out = append(out, map[string]any{"id": v.ID, "album": v.Album, "caption": v.Caption, "url": "/media/photos/" + v.ID})
		}
	}
	sort.Slice(out, func(i, j int) bool { return out[i]["id"].(string) < out[j]["id"].(string) })
	return out
}
func (a *App) media(w http.ResponseWriter, r *http.Request) {
	if r.Method != "GET" && r.Method != "HEAD" {
		w.WriteHeader(405)
		return
	}
	st := a.store.Snapshot()
	var b []byte
	name := ""
	if strings.HasPrefix(r.URL.Path, "/media/tracks/") {
		id := strings.TrimPrefix(r.URL.Path, "/media/tracks/")
		v, ok := st.Tracks[id]
		if ok && v.Published {
			b = v.Audio
			name = id + ".wav"
			w.Header().Set("Content-Type", "audio/wav")
		}
	}
	if strings.HasPrefix(r.URL.Path, "/media/photos/") {
		id := strings.TrimPrefix(r.URL.Path, "/media/photos/")
		v, ok := st.Photos[id]
		if ok && st.Albums[v.Album].Published {
			b = v.Data
			name = id
			w.Header().Set("Content-Type", http.DetectContentType(b))
		}
	}
	if b == nil {
		http.NotFound(w, r)
		return
	}
	http.ServeContent(w, r, name, time.Time{}, bytes.NewReader(b))
}
func validWAV(b []byte) bool {
	if len(b) < 44 || len(b) > 1<<20 || string(b[:4]) != "RIFF" || string(b[8:16]) != "WAVEfmt " || binary.LittleEndian.Uint32(b[4:8]) != uint32(len(b)-8) || binary.LittleEndian.Uint32(b[16:20]) != 16 || binary.LittleEndian.Uint16(b[20:22]) != 1 || string(b[36:40]) != "data" {
		return false
	}
	channels := binary.LittleEndian.Uint16(b[22:24])
	rate := binary.LittleEndian.Uint32(b[24:28])
	bits := binary.LittleEndian.Uint16(b[34:36])
	align := binary.LittleEndian.Uint16(b[32:34])
	size := binary.LittleEndian.Uint32(b[40:44])
	return channels >= 1 && channels <= 2 && rate >= 8000 && rate <= 48000 && bits == 16 && align == channels*2 && binary.LittleEndian.Uint32(b[28:32]) == rate*uint32(align) && size == uint32(len(b)-44) && size > 0 && size%uint32(align) == 0
}
func validImage(b []byte) bool {
	if len(b) == 0 || len(b) > 1<<20 {
		return false
	}
	cfg, kind, e := image.DecodeConfig(bytes.NewReader(b))
	if e != nil || (kind != "png" && kind != "jpeg") || cfg.Width <= 0 || cfg.Height <= 0 || cfg.Width > 4096 || cfg.Height > 4096 || cfg.Width*cfg.Height > 4000000 {
		return false
	}
	_, _, e = image.Decode(bytes.NewReader(b))
	return e == nil
}
