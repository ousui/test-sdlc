package main

import (
 "bytes"
 "encoding/json"
 "errors"
 "net/http"
 "net/http/httptest"
 "os"
 "path/filepath"
 "reflect"
 "sync"
 "testing"
)

func r2Revision(c *client, kind, id string) uint64 {
 if kind=="site" {return uint64(object(c.request("GET","/api/site",nil,nil))["revision"].(float64))}
 data:=object(c.request("GET","/api/admin/content",nil,nil));for _,v:=range data[kind].([]any){m:=v.(map[string]any);if m["id"]==id{return uint64(m["revision"].(float64))}}
 c.t.Fatal("missing versioned content");return 0
}
func r2Body(kind,id string,version any) map[string]any {b:=map[string]any{"Title":"edited title","Version":version};if kind!="site"{b["ID"]=id};return b}
func r2Raw(c *client,path string,b any,code int)*httptest.ResponseRecorder {w:=c.request("POST",path,b,nil);c.expect(w,code);return w}
func r2Bytes(t *testing.T,a *App)[]byte {t.Helper();b,e:=os.ReadFile(a.store.path);if e!=nil{t.Fatal(e)};return b}

func TestR2TwoEditorsConflictAndExplicitReread(t *testing.T) {
 for _,kind:=range []string{"site","tracks","albums"}{t.Run(kind,func(t *testing.T){
  a,c,_:=environment(t);id:="";if kind=="tracks"{id=createTrack(c,true)};if kind=="albums"{id=createAlbum(c,true)}
  first,second:=r2Revision(c,kind,id),r2Revision(c,kind,id);if first!=second{t.Fatal("editors did not read same version")}
  path:="/api/admin/"+kind;w:=r2Raw(c,path,r2Body(kind,id,first),200);if object(w)["revision"]!=float64(first+1){t.Fatal("success revision not exact increment")}
  disk:=r2Bytes(t,a);b:=r2Body(kind,id,second);b["Title"]="lost editor";w=r2Raw(c,path,b,409)
  if object(w)["code"]!="version_conflict"||!bytes.Equal(disk,r2Bytes(t,a)){t.Fatal("conflict not explicit or mutated disk")}
  current:=r2Revision(c,kind,id);if current!=first+1{t.Fatal("conflict incremented version")};b["Version"]=current;r2Raw(c,path,b,200)
  if r2Revision(c,kind,id)!=current+1{t.Fatal("reread could not update")}
 })}
}
func TestR2MissingInvalidAndStaleVersionsNeverBypass(t *testing.T) {
 a,c,_:=environment(t);id:=createTrack(c,true);path:="/api/admin/tracks";before:=r2Bytes(t,a)
 for _,v:=range []struct{value any;omit bool;code int}{{nil,true,428},{nil,false,428},{0,false,400},{-1,false,400},{1.5,false,400},{"1",false,400},{uint64(9007199254740992),false,400},{999,false,409}}{
  b:=r2Body("tracks",id,v.value);if v.omit{delete(b,"Version")};w:=r2Raw(c,path,b,v.code)
  if v.code==428&&object(w)["code"]!="version_required"{t.Fatal("missing version error not explicit")};if !bytes.Equal(before,r2Bytes(t,a)){t.Fatal("rejected version changed persisted data")}
 }
 r2Raw(c,path,map[string]any{"ID":"missing","Title":"x"},404)
 guest:=newClient(t,a);r2Raw(guest,path,r2Body("tracks",id,1),403)
 r2Raw(c,"/api/admin/delete",map[string]any{"Kind":"track","ID":id},428)
 r2Raw(c,"/api/admin/delete",map[string]any{"Kind":"track","ID":id,"Version":999},409)
}
func TestR2ConcurrentVersionSingleWinner(t *testing.T) {
 for _,kind:=range []string{"site","tracks","albums"}{t.Run(kind,func(t *testing.T){
  a,c,_:=environment(t);id:="";if kind=="tracks"{id=createTrack(c,true)};if kind=="albums"{id=createAlbum(c,true)};v:=r2Revision(c,kind,id)
  start:=make(chan struct{});codes:=make(chan int,8);var wg sync.WaitGroup
  for i:=0;i<8;i++{g:=&client{t:t,a:a,csrf:c.csrf,cookies:map[string]*http.Cookie{}};for k,v:=range c.cookies{copy:=*v;g.cookies[k]=&copy};wg.Add(1);go func(g *client){defer wg.Done();<-start;w:=g.request("POST","/api/admin/"+kind,r2Body(kind,id,v),nil);codes<-w.Code}(g)}
  close(start);wg.Wait();close(codes);success,conflict:=0,0;for code:=range codes{switch code{case 200:success++;case 409:conflict++;default:t.Fatalf("unexpected status %d",code)}}
  if success!=1||conflict!=7||r2Revision(c,kind,id)!=v+1{t.Fatalf("lost-update race success=%d conflict=%d",success,conflict)}
 })}
}
func TestR2PhotoMembershipParticipatesInAlbumVersion(t *testing.T) {
 a,c,_:=environment(t);al:=createAlbum(c,true);version:=r2Revision(c,"albums",al)
 b:=map[string]any{"Album":al,"Caption":"new","Data":picture()};r2Raw(c,"/api/admin/photos",b,428);b["AlbumVersion"]=version
 w:=r2Raw(c,"/api/admin/photos",b,200);ph:=object(w)["id"].(string);if r2Revision(c,"albums",al)!=version+1{t.Fatal("photo addition did not advance album")}
 before:=r2Bytes(t,a);r2Raw(c,"/api/admin/photos",b,409);if !bytes.Equal(before,r2Bytes(t,a))||len(a.store.Snapshot().Photos)!=1{t.Fatal("stale photo upload created a reference")}
 r2Raw(c,"/api/admin/delete",map[string]any{"Kind":"album","ID":al,"Version":version},409)
 r2Raw(c,"/api/admin/delete",map[string]any{"Kind":"photo","ID":ph,"Version":1},200);if r2Revision(c,"albums",al)!=version+2{t.Fatal("photo delete did not advance album")}
 c.expect(c.request("GET","/media/photos/"+ph,nil,nil),404)
}
func TestR2PersistenceFailurePreservesVersionsAndMedia(t *testing.T) {
 for _,operation:=range []string{"site","replace_audio","withdraw_track","withdraw_album","add_photo","delete_track","delete_album","delete_photo"}{t.Run(operation,func(t *testing.T){
  a,c,_:=environment(t);tr:=createTrack(c,true);al:=createAlbum(c,true);ph:=createPhoto(c,al);st:=a.store.Snapshot();disk:=r2Bytes(t,a);path:="";var body map[string]any
  switch operation{
  case "site":path="/api/admin/site";body=r2Body("site","",st.SiteRevision)
  case "replace_audio","withdraw_track":path="/api/admin/tracks";body=r2Body("tracks",tr,st.Tracks[tr].Revision);if operation=="replace_audio"{audio:=wave();audio[len(audio)-1]=23;body["Audio"]=audio}else{body["Status"]="withdrawn"}
  case "withdraw_album":path="/api/admin/albums";body=r2Body("albums",al,st.Albums[al].Revision);body["Status"]="withdrawn"
  case "add_photo":path="/api/admin/photos";body=map[string]any{"Album":al,"AlbumVersion":st.Albums[al].Revision,"Data":picture(),"Caption":"must not leak"}
  default:path="/api/admin/delete";kind:=operation[len("delete_"):];id:=tr;version:=st.Tracks[tr].Revision;if kind=="album"{id=al;version=st.Albums[al].Revision};if kind=="photo"{id=ph;version=st.Photos[ph].Revision};body=map[string]any{"Kind":kind,"ID":id,"Version":version}
  }
  persist:=a.store.persist;a.store.persist=func([]byte)error{return errors.New("injected durable write failure")};w:=r2Raw(c,path,body,500)
  if object(w)["id"]!=nil||object(w)["revision"]!=nil{t.Fatal("failed persistence returned success identity/version")}
  if !reflect.DeepEqual(st,a.store.Snapshot())||!bytes.Equal(disk,r2Bytes(t,a)){t.Fatal("failed persistence exposed partial content/revision/reference")}
  for _,url:=range []string{"/media/tracks/"+tr,"/media/photos/"+ph}{r1Media(c,url,true)}
  reopened,e:=OpenStore(filepath.Dir(a.store.path));if e!=nil{t.Fatal(e)};if !reflect.DeepEqual(st,reopened.Snapshot()){t.Fatal("restart after failure differed")}
  a.store.persist=persist;r2Raw(c,path,body,200)
  if operation=="delete_album"&&len(a.store.Snapshot().Photos)!=0{t.Fatal("successful cascade left orphan photo")}
  if operation=="withdraw_track"||operation=="delete_track"{r1Media(c,"/media/tracks/"+tr,false)}
  if operation=="withdraw_album"||operation=="delete_album"||operation=="delete_photo"{r1Media(c,"/media/photos/"+ph,false)}
 })}
}
func TestR2RealFilesystemFailurePreservesReadableState(t *testing.T) {
 a,c,_:=environment(t);id:=createTrack(c,true);before:=a.store.Snapshot();disk:=r2Bytes(t,a);path:=a.store.path;backup:=path+".kept"
 if e:=os.Rename(path,backup);e!=nil{t.Fatal(e)};if e:=os.Mkdir(path,0700);e!=nil{t.Fatal(e)}
 restored:=false;restore:=func(){if !restored{_ = os.Remove(path);_ = os.Rename(backup,path);restored=true}};defer restore()
 body:=r2Body("tracks",id,before.Tracks[id].Revision);body["Status"]="withdrawn";r2Raw(c,"/api/admin/tracks",body,500)
 saved,e:=os.ReadFile(backup);if e!=nil||!bytes.Equal(saved,disk)||!reflect.DeepEqual(before,a.store.Snapshot()){t.Fatal("filesystem failure lost old bytes or visible state")};r1Media(c,"/media/tracks/"+id,true)
 restore();reopened,e:=OpenStore(filepath.Dir(path));if e!=nil{t.Fatal(e)};if !reflect.DeepEqual(before,reopened.Snapshot()){t.Fatal("filesystem failure changed restart state")}
 r2Raw(c,"/api/admin/tracks",body,200);r1Media(c,"/media/tracks/"+id,false)
}
func TestR2RestartVersionConflictsAndDeletedURLs(t *testing.T) {
 a,c,phrase:=environment(t);tr:=createTrack(c,true);al:=createAlbum(c,true);ph:=createPhoto(c,al);old:=r2Revision(c,"tracks",tr)
 body:=r2Body("tracks",tr,old);body["Status"]="withdrawn";r2Raw(c,"/api/admin/tracks",body,200)
 r2Raw(c,"/api/admin/delete",map[string]any{"Kind":"album","ID":al,"Version":r2Revision(c,"albums",al)},200)
 reopened,e:=OpenStore(filepath.Dir(a.store.path));if e!=nil{t.Fatal(e)};b:=NewApp(reopened,false);login:=newClient(t,b);login.post("/api/login",map[string]string{"Email":"admin@example.invalid","Password":phrase},200)
 if r2Revision(login,"tracks",tr)!=old+1{t.Fatal("revision lost on restart")};r2Raw(login,"/api/admin/tracks",body,409)
 r1Media(login,"/media/tracks/"+tr,false);r1Media(login,"/media/photos/"+ph,false);login.expect(login.request("GET","/api/albums/"+al,nil,nil),404)
 body["Version"]=old+1;body["Status"]="published";r2Raw(login,"/api/admin/tracks",body,200);r1Media(login,"/media/tracks/"+tr,true)
}
func TestR2AdditiveRevisionMigrationPreservesQ1(t *testing.T) {
 a,c,_:=environment(t);tr:=createTrack(c,true);al:=createAlbum(c,true);ph:=createPhoto(c,al);st:=a.store.Snapshot();var legacy map[string]any;_ = json.Unmarshal(r2Bytes(t,a),&legacy);delete(legacy,"site_revision")
 for _,kind:=range []string{"tracks","albums","photos"}{for _,v:=range legacy[kind].(map[string]any){delete(v.(map[string]any),"revision")}}
 raw,_:=json.Marshal(legacy);dir:=t.TempDir();path:=filepath.Join(dir,"state.json");if e:=os.WriteFile(path,raw,0600);e!=nil{t.Fatal(e)};m,e:=OpenStore(dir);if e!=nil{t.Fatal(e)};next:=m.Snapshot()
 if next.Version!=2||next.SiteRevision!=1||next.Tracks[tr].Revision!=1||next.Albums[al].Revision!=1||next.Photos[ph].Revision!=1||!bytes.Equal(next.Tracks[tr].Audio,st.Tracks[tr].Audio)||!bytes.Equal(next.Photos[ph].Data,st.Photos[ph].Data)||!reflect.DeepEqual(next.Users,st.Users){t.Fatal("additive migration lost data")}
 disk,_:=os.ReadFile(path);if bytes.Equal(raw,disk){t.Fatal("revisions not persisted")};if _,e=OpenStore(dir);e!=nil{t.Fatal(e)};again,_:=os.ReadFile(path);if !bytes.Equal(disk,again){t.Fatal("reopen rewrote migration")}
}
func TestR2RevisionExhaustionAndHelperNeverReplacesExplicitInput(t *testing.T) {
 a,c,_:=environment(t);id:=createTrack(c,true);r2Raw(c,"/api/admin/tracks",r2Body("tracks",id,1),200)
 c.post("/api/admin/tracks",r2Body("tracks",id,1),409);c.post("/api/admin/tracks",r2Body("tracks",id,nil),428)
 if e:=a.store.Update(func(st *State)error{v:=st.Tracks[id];v.Revision=maxContentRevision;st.Tracks[id]=v;return nil});e!=nil{t.Fatal(e)};before:=r2Bytes(t,a)
 w:=r2Raw(c,"/api/admin/tracks",r2Body("tracks",id,maxContentRevision),409);if object(w)["code"]!="version_exhausted"||!bytes.Equal(before,r2Bytes(t,a)){t.Fatal("revision wrapped or exhaustion hidden")}
}
