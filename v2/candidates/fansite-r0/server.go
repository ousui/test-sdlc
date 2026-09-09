package main

import (
 "bytes"
 "crypto/sha256"
 "crypto/subtle"
 "embed"
 "encoding/binary"
 "encoding/hex"
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
 "unicode/utf8"
)

//go:embed web/*
var assets embed.FS

type Session struct { UserID string; Version uint64; CSRF string; Expires time.Time }
type App struct {
 store *Store
 secure bool
 now func() time.Time
 mu sync.Mutex
 sessions map[string]Session
 page *template.Template
}
func NewApp(store *Store, secure bool) *App {
 return &App{store:store, secure:secure, now:time.Now, sessions:map[string]Session{}, page:template.Must(template.ParseFS(assets,"web/index.html"))}
}
func sessionKey(raw string) string { sum:=sha256.Sum256([]byte(raw)); return hex.EncodeToString(sum[:]) }
func (a *App) newSession(w http.ResponseWriter, r *http.Request, user string, version uint64) Session {
 raw:=randomID(); s:=Session{UserID:user,Version:version,CSRF:randomID(),Expires:a.now().Add(24*time.Hour)}
 a.mu.Lock()
 if c,e:=r.Cookie("fans_session"); e==nil { delete(a.sessions,sessionKey(c.Value)) }
 for id,old:=range a.sessions { if !old.Expires.After(a.now()) { delete(a.sessions,id) } }
 a.sessions[sessionKey(raw)]=s; a.mu.Unlock()
 http.SetCookie(w,&http.Cookie{Name:"fans_session",Value:raw,Path:"/",HttpOnly:true,SameSite:http.SameSiteStrictMode,Secure:a.secure,MaxAge:86400})
 return s
}
func (a *App) session(r *http.Request) (Session,bool) {
 c,e:=r.Cookie("fans_session"); if e!=nil { return Session{},false }
 a.mu.Lock(); s,ok:=a.sessions[sessionKey(c.Value)]; a.mu.Unlock()
 if !ok||!s.Expires.After(a.now()) { return Session{},false }
 if s.UserID!="" { u,ok:=a.store.Snapshot().Users[s.UserID]; if !ok||!u.Enabled||u.SessionVersion!=s.Version { return Session{},false } }
 return s,true
}
func userView(u User) map[string]any { return map[string]any{"id":u.ID,"email":u.Email,"name":u.Name,"bio":u.Bio,"enabled":u.Enabled,"admin":u.Admin} }
func output(w http.ResponseWriter, status int, v any) { w.Header().Set("Content-Type","application/json; charset=utf-8"); w.WriteHeader(status); _=json.NewEncoder(w).Encode(v) }
func fail(w http.ResponseWriter, status int, message string) { output(w,status,map[string]string{"error":message}) }
func resultError(w http.ResponseWriter, err error) {
 switch { case errors.Is(err,errInvalid):fail(w,400,"invalid input"); case errors.Is(err,errConflict):fail(w,409,"already exists"); case errors.Is(err,errForbidden):fail(w,403,"access denied"); case errors.Is(err,errNotFound):fail(w,404,"not found"); default:fail(w,500,"storage operation failed") }
}
func decode(w http.ResponseWriter,r *http.Request,v any) bool {
 r.Body=http.MaxBytesReader(w,r.Body,2<<20)
 d:=json.NewDecoder(r.Body);d.DisallowUnknownFields()
 if e:=d.Decode(v);e!=nil { fail(w,400,"invalid JSON or request too large");return false }
 if e:=d.Decode(new(any));e!=io.EOF { fail(w,400,"only one JSON value is allowed");return false };return true
}
func validText(s string,max int,required bool) bool { return utf8.ValidString(s)&&utf8.RuneCountInString(s)<=max&&(!required||strings.TrimSpace(s)!="") }
func (a *App) updateAs(s Session,admin bool, fn func(*State,User)error) error {
 return a.store.Update(func(st *State)error{u,ok:=st.Users[s.UserID];if !ok||!u.Enabled||u.SessionVersion!=s.Version||(admin&&!u.Admin){return errForbidden};return fn(st,u)})
}
func trackViews(st State,admin bool) []any {
 ids:=make([]string,0,len(st.Tracks));for id:=range st.Tracks{ids=append(ids,id)};sort.Strings(ids);out:=[]any{}
 for _,id:=range ids {v:=st.Tracks[id];if admin||v.Published {out=append(out,map[string]any{"id":v.ID,"title":v.Title,"published":v.Published,"url":"/media/tracks/"+id})}};return out
}
func albumViews(st State,admin bool) []any {
 ids:=make([]string,0,len(st.Albums));for id:=range st.Albums{ids=append(ids,id)};sort.Strings(ids);out:=[]any{}
 for _,id:=range ids {v:=st.Albums[id];if admin||v.Published{out=append(out,map[string]any{"id":v.ID,"title":v.Title,"description":v.Description,"published":v.Published})}};return out
}
func photoViews(st State,album string) []any {
 ids:=[]string{};for id,p:=range st.Photos {if album==""||p.Album==album{ids=append(ids,id)}};sort.Strings(ids);out:=[]any{}
 for _,id:=range ids {p:=st.Photos[id];out=append(out,map[string]any{"id":id,"album":p.Album,"caption":p.Caption,"url":"/media/photos/"+id})};return out
}
func validWave(b []byte) bool {
 if len(b)<44||len(b)>1<<20||string(b[:4])!="RIFF"||string(b[8:12])!="WAVE"||int(binary.LittleEndian.Uint32(b[4:8]))!=len(b)-8{return false}
 fmtOK,dataOK:=false,false;block:=0;dataSize:=0
 for offset:=12;offset+8<=len(b); {
  tag:=string(b[offset:offset+4]);size:=int(binary.LittleEndian.Uint32(b[offset+4:offset+8]));start:=offset+8
  if size>len(b)-start{return false}
  if tag=="fmt " {
   if size<16{return false};x:=b[start:start+size];channels:=int(binary.LittleEndian.Uint16(x[2:4]));rate:=int(binary.LittleEndian.Uint32(x[4:8]));bits:=int(binary.LittleEndian.Uint16(x[14:16]));block=int(binary.LittleEndian.Uint16(x[12:14]))
   fmtOK=binary.LittleEndian.Uint16(x[:2])==1&&(channels==1||channels==2)&&rate>0&&rate<=192000&&(bits==8||bits==16||bits==24||bits==32)&&block==channels*bits/8&&int(binary.LittleEndian.Uint32(x[8:12]))==rate*block
  }
  if tag=="data" {dataOK=size>0;dataSize=size};offset=start+size+(size%2)
 }
 return fmtOK&&dataOK&&block>0&&dataSize%block==0
}
func validPicture(b []byte) bool {
 if len(b)==0||len(b)>1<<20{return false}
 config,format,e:=image.DecodeConfig(bytes.NewReader(b));if e!=nil||(format!="png"&&format!="jpeg")||config.Width<=0||config.Height<=0||config.Width>4096||config.Height>4096||config.Width*config.Height>16000000{return false}
 _,_,e=image.Decode(bytes.NewReader(b));return e==nil
}
func (a *App) ServeHTTP(w http.ResponseWriter,r *http.Request) {
 w.Header().Set("X-Content-Type-Options","nosniff")
 w.Header().Set("Content-Security-Policy","default-src 'self'; img-src 'self'; media-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'self'")
 w.Header().Set("Cache-Control","no-store")
 path:=r.URL.Path
 if strings.HasPrefix(path,"/api/"){a.api(w,r);return}
 if strings.HasPrefix(path,"/media/"){a.media(w,r);return}
 if r.Method!="GET"&&r.Method!="HEAD" {fail(w,405,"method not allowed");return}
 if path=="/assets/app.js"||path=="/assets/style.css" {
  name:="web/"+strings.TrimPrefix(path,"/assets/");raw,e:=assets.ReadFile(name);if e!=nil{http.NotFound(w,r);return}
  if strings.HasSuffix(name,".js"){w.Header().Set("Content-Type","text/javascript; charset=utf-8")}else{w.Header().Set("Content-Type","text/css; charset=utf-8")}
  if r.Method!="HEAD"{_,_=w.Write(raw)};return
 }
 pages:=map[string]string{"/":"home","/music":"music","/albums":"albums","/login":"login","/register":"register","/profile":"profile","/admin":"admin"}
 page,ok:=pages[path];if !ok {http.NotFound(w,r);return}
 if page=="profile"||page=="admin" {
  s,ok:=a.session(r);if !ok||s.UserID=="" {http.Redirect(w,r,"/login",303);return}
  if page=="admin"&&!a.store.Snapshot().Users[s.UserID].Admin{fail(w,403,"access denied");return}
 }
 st:=a.store.Snapshot();w.Header().Set("Content-Type","text/html; charset=utf-8")
 if r.Method!="HEAD"{_ = a.page.Execute(w,map[string]string{"Title":st.Title,"Intro":st.Intro,"Page":page})}
}
func (a *App) api(w http.ResponseWriter,r *http.Request) {
 path:=r.URL.Path;s,valid:=a.session(r);var u User;if valid&&s.UserID!=""{u=a.store.Snapshot().Users[s.UserID]}
 if r.Method=="GET" {
  st:=a.store.Snapshot()
  switch path {
  case "/api/session":if !valid{s=a.newSession(w,r,"",0)};view:=map[string]any{"csrf_token":s.CSRF};if u.ID!=""{view["user"]=userView(u)};output(w,200,view)
  case "/api/site":output(w,200,map[string]string{"title":st.Title,"intro":st.Intro})
  case "/api/tracks":output(w,200,trackViews(st,false))
  case "/api/albums":output(w,200,albumViews(st,false))
  case "/api/me":if u.ID==""{fail(w,403,"login required");return};output(w,200,userView(u))
  case "/api/admin/users":if !u.Admin{fail(w,403,"administrator required");return};ids:=[]string{};for id:=range st.Users{ids=append(ids,id)};sort.Strings(ids);users:=[]any{};for _,id:=range ids{users=append(users,userView(st.Users[id]))};output(w,200,users)
  case "/api/admin/content":if !u.Admin{fail(w,403,"administrator required");return};output(w,200,map[string]any{"tracks":trackViews(st,true),"albums":albumViews(st,true),"photos":photoViews(st,"")})
  case "/api/login","/api/register","/api/logout":fail(w,405,"POST required")
  default:
   if strings.HasPrefix(path,"/api/albums/"){id:=strings.TrimPrefix(path,"/api/albums/");al,ok:=st.Albums[id];if !ok||!al.Published{fail(w,404,"album not found");return};output(w,200,map[string]any{"id":al.ID,"title":al.Title,"description":al.Description,"photos":photoViews(st,id)});return};fail(w,404,"not found")
  };return
 }
 if r.Method!="POST"{fail(w,405,"method not allowed");return}
 typ,_,e:=mime.ParseMediaType(r.Header.Get("Content-Type"));if e!=nil||typ!="application/json"{fail(w,415,"application/json required");return}
 if !valid||subtle.ConstantTimeCompare([]byte(s.CSRF),[]byte(r.Header.Get("X-CSRF-Token")))!=1{fail(w,403,"invalid session or CSRF");return}
 if origin:=r.Header.Get("Origin");origin!=""{o,e:=url.Parse(origin);scheme:="http";if r.TLS!=nil{scheme="https"};if e!=nil||o.Host!=r.Host||o.Scheme!=scheme||o.User!=nil{fail(w,403,"invalid origin");return}}
 if strings.HasPrefix(path,"/api/admin/")&&!u.Admin{fail(w,403,"administrator required");return}
 switch path {
 case "/api/register":
  var in struct{Email,Password,Name string};if !decode(w,r,&in){return};user,e:=a.store.Register(in.Email,in.Password,in.Name,false);if e!=nil{resultError(w,e);return};fresh:=a.newSession(w,r,user.ID,user.SessionVersion);output(w,201,map[string]any{"user":userView(user),"csrf_token":fresh.CSRF})
 case "/api/login":
  var in struct{Email,Password string};if !decode(w,r,&in){return};user,e:=a.store.Authenticate(in.Email,in.Password);if e!=nil{resultError(w,e);return};fresh:=a.newSession(w,r,user.ID,user.SessionVersion);output(w,200,map[string]any{"user":userView(user),"csrf_token":fresh.CSRF})
 case "/api/logout":
  var in struct{};if !decode(w,r,&in){return};a.mu.Lock();if c,e:=r.Cookie("fans_session");e==nil{delete(a.sessions,sessionKey(c.Value))};a.mu.Unlock();http.SetCookie(w,&http.Cookie{Name:"fans_session",Path:"/",MaxAge:-1,HttpOnly:true,SameSite:http.SameSiteStrictMode,Secure:a.secure});output(w,200,map[string]bool{"ok":true})
 case "/api/me":
  var in struct{Name,Bio string};if !decode(w,r,&in){return};if !validText(in.Name,80,false)||!validText(in.Bio,1000,false){resultError(w,errInvalid);return}
  e:=a.updateAs(s,false,func(st *State,user User)error{user.Name=in.Name;user.Bio=in.Bio;st.Users[user.ID]=user;return nil});if e!=nil{resultError(w,e);return};output(w,200,userView(a.store.Snapshot().Users[s.UserID]))
 case "/api/admin/site":
  var in struct{Title,Intro string};if !decode(w,r,&in){return};if !validText(in.Title,160,true)||!validText(in.Intro,4000,false){resultError(w,errInvalid);return}
  e:=a.updateAs(s,true,func(st *State,_ User)error{st.Title=in.Title;st.Intro=in.Intro;return nil});if e!=nil{resultError(w,e);return};output(w,200,map[string]bool{"ok":true})
 case "/api/admin/user-state":
  var in struct{ID string;Enabled bool};if !decode(w,r,&in){return}
  e:=a.updateAs(s,true,func(st *State,_ User)error{target,ok:=st.Users[in.ID];if !ok{return errNotFound};if target.Admin{return errForbidden};if target.Enabled!=in.Enabled{target.SessionVersion++};target.Enabled=in.Enabled;st.Users[in.ID]=target;return nil});if e!=nil{resultError(w,e);return};output(w,200,map[string]bool{"ok":true})
 case "/api/admin/tracks":
  var in struct{ID,Title string;Published *bool;Audio []byte};if !decode(w,r,&in){return};if !validText(in.Title,160,true)||(len(in.Audio)>0&&!validWave(in.Audio)){resultError(w,errInvalid);return}
  id:=in.ID;if id==""{id=randomID()}
  e:=a.updateAs(s,true,func(st *State,_ User)error{track,ok:=st.Tracks[id];if in.ID!=""&&!ok{return errNotFound};if in.ID==""&&!validWave(in.Audio){return errInvalid};track.ID=id;track.Title=in.Title;if len(in.Audio)>0{track.Audio=append([]byte(nil),in.Audio...)};if in.Published!=nil{track.Published=*in.Published};st.Tracks[id]=track;return nil});if e!=nil{resultError(w,e);return};output(w,200,map[string]string{"id":id})
 case "/api/admin/albums":
  var in struct{ID,Title,Description string;Published *bool};if !decode(w,r,&in){return};if !validText(in.Title,160,true)||!validText(in.Description,2000,false){resultError(w,errInvalid);return};id:=in.ID;if id==""{id=randomID()}
  e:=a.updateAs(s,true,func(st *State,_ User)error{al,ok:=st.Albums[id];if in.ID!=""&&!ok{return errNotFound};al.ID=id;al.Title=in.Title;al.Description=in.Description;if in.Published!=nil{al.Published=*in.Published};st.Albums[id]=al;return nil});if e!=nil{resultError(w,e);return};output(w,200,map[string]string{"id":id})
 case "/api/admin/photos":
  var in struct{Album,Caption string;Data []byte};if !decode(w,r,&in){return};if !validPicture(in.Data)||!validText(in.Caption,300,false){resultError(w,errInvalid);return};id:=randomID()
  e:=a.updateAs(s,true,func(st *State,_ User)error{if _,ok:=st.Albums[in.Album];!ok{return errNotFound};st.Photos[id]=Photo{ID:id,Album:in.Album,Caption:in.Caption,Data:append([]byte(nil),in.Data...)};return nil});if e!=nil{resultError(w,e);return};output(w,200,map[string]string{"id":id})
 case "/api/admin/delete":
  var in struct{Kind,ID string};if !decode(w,r,&in){return}
  e:=a.updateAs(s,true,func(st *State,_ User)error{switch in.Kind{case "track":if _,ok:=st.Tracks[in.ID];!ok{return errNotFound};delete(st.Tracks,in.ID);case "album":if _,ok:=st.Albums[in.ID];!ok{return errNotFound};delete(st.Albums,in.ID);for id,p:=range st.Photos{if p.Album==in.ID{delete(st.Photos,id)}};case "photo":if _,ok:=st.Photos[in.ID];!ok{return errNotFound};delete(st.Photos,in.ID);default:return errInvalid};return nil});if e!=nil{resultError(w,e);return};output(w,200,map[string]bool{"ok":true})
 default:fail(w,404,"not found")
 }
}
func (a *App) media(w http.ResponseWriter,r *http.Request) {
 if r.Method!="GET"&&r.Method!="HEAD"{fail(w,405,"method not allowed");return};st:=a.store.Snapshot()
 if strings.HasPrefix(r.URL.Path,"/media/tracks/"){id:=strings.TrimPrefix(r.URL.Path,"/media/tracks/");v,ok:=st.Tracks[id];if !ok||!v.Published{http.NotFound(w,r);return};w.Header().Set("Content-Type","audio/wav");http.ServeContent(w,r,v.Title,time.Time{},bytes.NewReader(v.Audio));return}
 if strings.HasPrefix(r.URL.Path,"/media/photos/"){id:=strings.TrimPrefix(r.URL.Path,"/media/photos/");v,ok:=st.Photos[id];al,exists:=st.Albums[v.Album];if !ok||!exists||!al.Published{http.NotFound(w,r);return};w.Header().Set("Content-Type",http.DetectContentType(v.Data));http.ServeContent(w,r,v.Caption,time.Time{},bytes.NewReader(v.Data));return};http.NotFound(w,r)
}
