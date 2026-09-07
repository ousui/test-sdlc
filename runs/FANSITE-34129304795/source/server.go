package main

import (
 "bytes"
 "crypto/sha256"
 "crypto/subtle"
 "embed"
 "encoding/hex"
 "encoding/json"
 "errors"
 "html/template"
 "image"
 _ "image/jpeg"
 _ "image/png"
 "io"
 "net/http"
 "net/url"
 "strings"
 "sync"
 "time"
)

//go:embed web
var assets embed.FS

type App struct { store *Store; mux *http.ServeMux; mu sync.Mutex; sessions map[string]Session; secure bool; now func()time.Time; authSlots chan struct{} }
func NewApp(s *Store,secure bool)*App {
 a:=&App{store:s,mux:http.NewServeMux(),sessions:map[string]Session{},secure:secure,now:time.Now,authSlots:make(chan struct{},4)}
 a.mux.HandleFunc("/api/session",a.current)
 a.mux.HandleFunc("/api/register",a.register)
 a.mux.HandleFunc("/api/login",a.login)
 a.mux.HandleFunc("/api/logout",a.logout)
 a.mux.HandleFunc("/api/me",a.profile)
 a.mux.HandleFunc("/api/site",a.site)
 a.mux.HandleFunc("/api/tracks",a.tracks)
 a.mux.HandleFunc("/api/albums",a.albums)
 a.mux.HandleFunc("/api/albums/",a.album)
 a.mux.HandleFunc("/media/tracks/",a.audio)
 a.mux.HandleFunc("/media/photos/",a.photo)
 a.mux.HandleFunc("/api/admin/",a.admin)
 a.mux.HandleFunc("/assets/",a.static)
 a.mux.HandleFunc("/",a.page)
 return a
}
func(a *App) ServeHTTP(w http.ResponseWriter,r *http.Request){
 w.Header().Set("X-Content-Type-Options","nosniff");w.Header().Set("X-Frame-Options","DENY")
 w.Header().Set("Content-Security-Policy","default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self'; media-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
 w.Header().Set("Referrer-Policy","no-referrer");w.Header().Set("Cache-Control","no-store");a.mux.ServeHTTP(w,r)
}
func reply(w http.ResponseWriter,status int,v any){w.Header().Set("Content-Type","application/json; charset=utf-8");w.WriteHeader(status);_ = json.NewEncoder(w).Encode(v)}
func fail(w http.ResponseWriter,e error){c:=500;m:="storage unavailable";switch{case errors.Is(e,errInput):c=400;m="invalid input";case errors.Is(e,errDenied):c=403;m="not authorized";case errors.Is(e,errNotFound):c=404;m="not found";case errors.Is(e,errConflict):c=409;m="conflict"};reply(w,c,map[string]string{"error":m})}
func method(w http.ResponseWriter,r *http.Request,m string)bool{if r.Method!=m{w.Header().Set("Allow",m);reply(w,405,map[string]string{"error":"method not allowed"});return false};return true}
func decode(w http.ResponseWriter,r *http.Request,v any)bool{
 if !strings.HasPrefix(r.Header.Get("Content-Type"),"application/json"){reply(w,415,map[string]string{"error":"JSON required"});return false}
 r.Body=http.MaxBytesReader(w,r.Body,2<<20);d:=json.NewDecoder(r.Body);d.DisallowUnknownFields()
 if e:=d.Decode(v);e!=nil{fail(w,errInput);return false};var extra any;if d.Decode(&extra)!=io.EOF{fail(w,errInput);return false};return true
}
func key(v string)string{h:=sha256.Sum256([]byte(v));return hex.EncodeToString(h[:])}
func publicUser(u User)map[string]any{return map[string]any{"id":u.ID,"email":u.Email,"name":u.Name,"bio":u.Bio,"admin":u.Admin,"enabled":u.Enabled}}
func(a *App) session(r *http.Request)(Session,string,bool){
 c,e:=r.Cookie("fans_session");if e!=nil||len(c.Value)!=64{return Session{},"",false};k:=key(c.Value)
 a.mu.Lock();s,ok:=a.sessions[k];if ok&&!a.now().Before(s.Expires){delete(a.sessions,k);ok=false};a.mu.Unlock()
 if ok&&s.UserID!=""{u,exists:=a.store.Snapshot().Users[s.UserID];if !exists||!u.Enabled||u.SessionVersion!=s.Version{a.mu.Lock();delete(a.sessions,k);a.mu.Unlock();ok=false}}
 return s,k,ok
}
func(a *App) newSession(w http.ResponseWriter,r *http.Request,user string,version uint64)Session{
 raw:=randomID();s:=Session{UserID:user,Version:version,CSRF:randomID(),Expires:a.now().Add(24*time.Hour)}
 _,old,_:=a.session(r);a.mu.Lock();delete(a.sessions,old)
 for k,v:=range a.sessions{if !a.now().Before(v.Expires){delete(a.sessions,k)}};a.sessions[key(raw)]=s;a.mu.Unlock()
 http.SetCookie(w,&http.Cookie{Name:"fans_session",Value:raw,Path:"/",HttpOnly:true,Secure:a.secure||r.TLS!=nil,SameSite:http.SameSiteStrictMode,MaxAge:86400});return s
}
func(a *App) current(w http.ResponseWriter,r *http.Request){if !method(w,r,"GET"){return};s,_,ok:=a.session(r);if !ok{s=a.newSession(w,r,"",0)};var u any;if s.UserID!=""{u=publicUser(a.store.Snapshot().Users[s.UserID])};reply(w,200,map[string]any{"csrf_token":s.CSRF,"user":u})}
func(a *App) mutation(w http.ResponseWriter,r *http.Request,auth bool)(Session,bool){
 if !method(w,r,"POST"){return Session{},false}
 if origin:=r.Header.Get("Origin");origin!=""{u,e:=url.Parse(origin);if e!=nil||u.Host!=r.Host||(u.Scheme!="http"&&u.Scheme!="https"){fail(w,errDenied);return Session{},false}}
 s,_,ok:=a.session(r);provided:=r.Header.Get("X-CSRF-Token")
 if !ok||(auth&&s.UserID=="")||len(provided)!=64||subtle.ConstantTimeCompare([]byte(provided),[]byte(s.CSRF))!=1{fail(w,errDenied);return Session{},false};return s,true
}
func(a *App) register(w http.ResponseWriter,r *http.Request){
 if _,ok:=a.mutation(w,r,false);!ok{return};var in struct{Email,Password,Name string};if !decode(w,r,&in){return}
 select{case a.authSlots<-struct{}{}:defer func(){<-a.authSlots}();default:reply(w,429,map[string]string{"error":"try later"});return}
 u,e:=a.store.Register(in.Email,in.Password,in.Name,false);if e!=nil{fail(w,e);return};s:=a.newSession(w,r,u.ID,u.SessionVersion);reply(w,201,map[string]any{"user":publicUser(u),"csrf_token":s.CSRF})
}
func(a *App) login(w http.ResponseWriter,r *http.Request){
 if _,ok:=a.mutation(w,r,false);!ok{return};var in struct{Email,Password string};if !decode(w,r,&in){return}
 select{case a.authSlots<-struct{}{}:defer func(){<-a.authSlots}();default:reply(w,429,map[string]string{"error":"try later"});return}
 u,e:=a.store.Authenticate(in.Email,in.Password);if e!=nil{fail(w,errDenied);return};s:=a.newSession(w,r,u.ID,u.SessionVersion);reply(w,200,map[string]any{"user":publicUser(u),"csrf_token":s.CSRF})
}
func(a *App) logout(w http.ResponseWriter,r *http.Request){if _,ok:=a.mutation(w,r,true);!ok{return};_,k,_:=a.session(r);a.mu.Lock();delete(a.sessions,k);a.mu.Unlock();http.SetCookie(w,&http.Cookie{Name:"fans_session",Path:"/",MaxAge:-1,HttpOnly:true,Secure:a.secure,SameSite:http.SameSiteStrictMode});reply(w,200,map[string]bool{"ok":true})}
func(a *App) profile(w http.ResponseWriter,r *http.Request){
 if r.Method=="GET"{s,_,ok:=a.session(r);if !ok||s.UserID==""{fail(w,errDenied);return};reply(w,200,publicUser(a.store.Snapshot().Users[s.UserID]));return}
 s,ok:=a.mutation(w,r,true);if !ok{return};var in struct{Name,Bio string};if !decode(w,r,&in){return};if !cleanText(in.Name,80)||!cleanText(in.Bio,500){fail(w,errInput);return}
 e:=a.store.Update(func(st *State)error{u:=st.Users[s.UserID];u.Name=in.Name;u.Bio=in.Bio;st.Users[u.ID]=u;return nil});if e!=nil{fail(w,e);return};reply(w,200,publicUser(a.store.Snapshot().Users[s.UserID]))
}
func(a *App) site(w http.ResponseWriter,r *http.Request){if !method(w,r,"GET"){return};s:=a.store.Snapshot();reply(w,200,map[string]string{"title":s.Title,"intro":s.Intro,"notice":"非官方粉丝站；媒体仅为功能测试素材"})}
func trackView(t Track)map[string]any{return map[string]any{"id":t.ID,"title":t.Title,"published":t.Published,"url":"/media/tracks/"+t.ID}}
func albumView(v Album)map[string]any{p:=make([]any,0,len(v.Photos));for _,id:=range sortedKeys(v.Photos){ph:=v.Photos[id];p=append(p,map[string]string{"id":ph.ID,"caption":ph.Caption,"url":"/media/photos/"+ph.ID})};return map[string]any{"id":v.ID,"title":v.Title,"description":v.Description,"published":v.Published,"photos":p}}
func(a *App) tracks(w http.ResponseWriter,r *http.Request){if !method(w,r,"GET"){return};st:=a.store.Snapshot();v:=[]any{};for _,id:=range sortedKeys(st.Tracks){t:=st.Tracks[id];if t.Published{v=append(v,trackView(t))}};reply(w,200,v)}
func(a *App) albums(w http.ResponseWriter,r *http.Request){if !method(w,r,"GET"){return};st:=a.store.Snapshot();v:=[]any{};for _,id:=range sortedKeys(st.Albums){al:=st.Albums[id];if al.Published{v=append(v,albumView(al))}};reply(w,200,v)}
func(a *App) album(w http.ResponseWriter,r *http.Request){if !method(w,r,"GET"){return};id:=strings.TrimPrefix(r.URL.Path,"/api/albums/");al,ok:=a.store.Snapshot().Albums[id];if !ok||!al.Published{fail(w,errNotFound);return};reply(w,200,albumView(al))}
func media(w http.ResponseWriter,r *http.Request,name,ct string,data []byte){if r.Method!="GET"&&r.Method!="HEAD"{w.Header().Set("Allow","GET, HEAD");w.WriteHeader(405);return};w.Header().Set("Content-Type",ct);http.ServeContent(w,r,name,time.Time{},bytes.NewReader(data))}
func(a *App) audio(w http.ResponseWriter,r *http.Request){id:=strings.TrimPrefix(r.URL.Path,"/media/tracks/");t,ok:=a.store.Snapshot().Tracks[id];if !ok||!t.Published{fail(w,errNotFound);return};media(w,r,"preview.wav","audio/wav",t.Audio)}
func(a *App) photo(w http.ResponseWriter,r *http.Request){id:=strings.TrimPrefix(r.URL.Path,"/media/photos/");for _,al:=range a.store.Snapshot().Albums{if al.Published{if ph,ok:=al.Photos[id];ok{media(w,r,"photo",ph.ContentType,ph.Data);return}}};fail(w,errNotFound)}
func validWave(b []byte)bool{return len(b)>=44&&len(b)<=1<<20&&string(b[:4])=="RIFF"&&string(b[8:12])=="WAVE"&&string(b[12:16])=="fmt "}
func validImage(b []byte)(string,bool){if len(b)==0||len(b)>1<<20{return "",false};c,f,e:=image.DecodeConfig(bytes.NewReader(b));if e!=nil||c.Width<1||c.Height<1||c.Width>4096||c.Height>4096||c.Width*c.Height>16000000||(f!="png"&&f!="jpeg"){return "",false};_,_,e=image.Decode(bytes.NewReader(b));return "image/"+f,e==nil}
func(a *App) admin(w http.ResponseWriter,r *http.Request){
 s,_,ok:=a.session(r);if !ok||s.UserID==""||!a.store.Snapshot().Users[s.UserID].Admin{fail(w,errDenied);return}
 if r.Method=="GET"{
  st:=a.store.Snapshot();switch r.URL.Path{case "/api/admin/users":v:=[]any{};for _,id:=range sortedKeys(st.Users){v=append(v,publicUser(st.Users[id]))};reply(w,200,v)
  case "/api/admin/content":ts:=[]any{};als:=[]any{};for _,id:=range sortedKeys(st.Tracks){ts=append(ts,trackView(st.Tracks[id]))};for _,id:=range sortedKeys(st.Albums){als=append(als,albumView(st.Albums[id]))};reply(w,200,map[string]any{"tracks":ts,"albums":als,"title":st.Title,"intro":st.Intro})
  default:fail(w,errNotFound)};return
 }
 if _,ok=a.mutation(w,r,true);!ok{return};var e error;var result any=map[string]bool{"ok":true}
 switch r.URL.Path{
 case "/api/admin/site":var in struct{Title,Intro string};if !decode(w,r,&in){return};if strings.TrimSpace(in.Title)==""||!cleanText(in.Title,100)||!cleanText(in.Intro,2000){fail(w,errInput);return};e=a.store.Update(func(st *State)error{st.Title=in.Title;st.Intro=in.Intro;return nil})
 case "/api/admin/user-state":var in struct{ID string;Enabled bool};if !decode(w,r,&in){return};e=a.store.Update(func(st *State)error{u,ok:=st.Users[in.ID];if !ok{return errNotFound};if u.Admin&&!in.Enabled{return errDenied};if u.Enabled&&!in.Enabled{u.SessionVersion++};u.Enabled=in.Enabled;st.Users[in.ID]=u;return nil});if e==nil&&!in.Enabled{a.mu.Lock();for k,v:=range a.sessions{if v.UserID==in.ID{delete(a.sessions,k)}};a.mu.Unlock()}
 case "/api/admin/tracks":var in struct{ID,Title string;Published bool;Audio []byte};if !decode(w,r,&in){return};if strings.TrimSpace(in.Title)==""||!cleanText(in.Title,100)||(len(in.Audio)>0&&!validWave(in.Audio)){fail(w,errInput);return};e=a.store.Update(func(st *State)error{t:=Track{ID:in.ID};if in.ID!=""{var ok bool;t,ok=st.Tracks[in.ID];if !ok{return errNotFound}}else{t.ID=randomID()};if len(in.Audio)>0{t.Audio=in.Audio};if !validWave(t.Audio){return errInput};t.Title=in.Title;t.Published=in.Published;st.Tracks[t.ID]=t;result=trackView(t);return nil})
 case "/api/admin/albums":var in struct{ID,Title,Description string;Published bool};if !decode(w,r,&in){return};if strings.TrimSpace(in.Title)==""||!cleanText(in.Title,100)||!cleanText(in.Description,500){fail(w,errInput);return};e=a.store.Update(func(st *State)error{al:=Album{ID:in.ID,Photos:map[string]Photo{}};if in.ID!=""{var ok bool;al,ok=st.Albums[in.ID];if !ok{return errNotFound}}else{al.ID=randomID()};al.Title=in.Title;al.Description=in.Description;al.Published=in.Published;st.Albums[al.ID]=al;result=albumView(al);return nil})
 case "/api/admin/photos":var in struct{Album,Caption string;Data []byte};if !decode(w,r,&in){return};ct,ok:=validImage(in.Data);if !ok||!cleanText(in.Caption,200){fail(w,errInput);return};e=a.store.Update(func(st *State)error{al,ok:=st.Albums[in.Album];if !ok{return errNotFound};ph:=Photo{ID:randomID(),Caption:in.Caption,ContentType:ct,Data:in.Data};al.Photos[ph.ID]=ph;st.Albums[in.Album]=al;result=map[string]string{"id":ph.ID};return nil})
 case "/api/admin/delete":var in struct{Kind,ID string};if !decode(w,r,&in){return};e=a.store.Update(func(st *State)error{switch in.Kind{case "track":if _,ok:=st.Tracks[in.ID];!ok{return errNotFound};delete(st.Tracks,in.ID);case "album":if _,ok:=st.Albums[in.ID];!ok{return errNotFound};delete(st.Albums,in.ID);case "photo":found:=false;for id,al:=range st.Albums{if _,ok:=al.Photos[in.ID];ok{delete(al.Photos,in.ID);st.Albums[id]=al;found=true}};if !found{return errNotFound};default:return errInput};return nil})
 default:fail(w,errNotFound);return
 };if e!=nil{fail(w,e);return};reply(w,200,result)
}
func(a *App) static(w http.ResponseWriter,r *http.Request){if r.Method!="GET"{w.WriteHeader(405);return};name:=strings.TrimPrefix(r.URL.Path,"/assets/");if name!="app.js"&&name!="style.css"{http.NotFound(w,r);return};b,e:=assets.ReadFile("web/"+name);if e!=nil{http.NotFound(w,r);return};ct:="text/javascript; charset=utf-8";if name=="style.css"{ct="text/css; charset=utf-8"};w.Header().Set("Content-Type",ct);w.Write(b)}
func(a *App) page(w http.ResponseWriter,r *http.Request){
 if !method(w,r,"GET"){return};name:=strings.TrimPrefix(r.URL.Path,"/");switch name{case "","login","register","profile","music","albums","admin":default:http.NotFound(w,r);return}
 if name=="profile"||name=="admin"{s,_,ok:=a.session(r);if !ok||s.UserID==""{http.Redirect(w,r,"/login",303);return};if name=="admin"&&!a.store.Snapshot().Users[s.UserID].Admin{fail(w,errDenied);return}}
 t,e:=template.ParseFS(assets,"web/index.html");if e!=nil{http.Error(w,"template unavailable",500);return};w.Header().Set("Content-Type","text/html; charset=utf-8");t.Execute(w,map[string]string{"Page":name,"Title":a.store.Snapshot().Title})
}
