package main

import (
 "bytes"
 "encoding/json"
 "fmt"
 "net/http"
 "os"
 "path/filepath"
 "reflect"
 "strings"
 "testing"
)

type r1Page struct { Items []struct{ID,Title,Description,Status,URL string; Published bool} `json:"items"`; Total,Page int; PageSize int `json:"page_size"` }
func r1Get(c *client,path string) r1Page { c.t.Helper();w:=c.request("GET",path,nil,nil);c.expect(w,200);var p r1Page;if e:=json.Unmarshal(w.Body.Bytes(),&p);e!=nil{c.t.Fatal(e)};if p.Items==nil{c.t.Fatal("items must be an array, including empty results")};return p }
func r1IDs(p r1Page) []string { ids:=[]string{};for _,r:=range p.Items{ids=append(ids,r.ID)};return ids }
func r1Seed(t *testing.T,a *App) {
 t.Helper();if e:=a.store.Update(func(st *State)error{
  for i:=0;i<12;i++{id:=fmt.Sprintf("%02d",i);st.Tracks["t"+id]=Track{ID:"t"+id,Title:"Song",Published:true,Status:"published",Audio:wave()};st.Albums["a"+id]=Album{ID:"a"+id,Title:"Song",Description:"Summer Sessions",Published:true,Status:"published"}}
  for _,s:=range []string{"draft","withdrawn"}{st.Tracks["t-"+s]=Track{ID:"t-"+s,Title:"Hidden "+s,Status:s,Audio:wave()};st.Albums["a-"+s]=Album{ID:"a-"+s,Title:"Hidden "+s,Description:"Summer hidden",Status:s}}
  return nil
 });e!=nil{t.Fatal(e)}
}
func TestR1CatalogPaginationBoundaries(t *testing.T) {
 a,_,_:=environment(t);r1Seed(t,a);guest:=newClient(t,a)
 for _,kind:=range []string{"tracks","albums"}{t.Run(kind,func(t *testing.T){
  path:="/api/catalog/"+kind;p:=r1Get(guest,path)
  if p.Total!=12||p.Page!=1||p.PageSize!=10||len(p.Items)!=10{t.Fatalf("default page: %+v",p)}
  first:=r1IDs(p);second:=r1Get(guest,path+"?page=2");if second.Total!=12||len(second.Items)!=2{t.Fatal("last page")}
  joined:=append(first,r1IDs(second)...);prefix:="t";if kind=="albums"{prefix="a"};for i,id:=range joined{if id!=fmt.Sprintf("%s%02d",prefix,i){t.Fatalf("missing/repeated row %v",joined)}}
  for _,suffix:=range []string{"?page=3","?page=9223372036854775807","?q=does-not-exist"}{empty:=r1Get(guest,path+suffix);if len(empty.Items)!=0{t.Fatal("expected empty page")};if suffix!="?q=does-not-exist"&&empty.Total!=12{t.Fatal("total was paginated")}}
  one:=r1Get(guest,path+"?page_size=1");if len(one.Items)!=1||one.Total!=12{t.Fatal("minimum size")}
  hundred:=r1Get(guest,path+"?page_size=100");if len(hundred.Items)!=12{t.Fatal("maximum size")}
 })}
}
func TestR1StableTitleTiesAndRepeatedPages(t *testing.T) {
 a,_,_:=environment(t)
 if e:=a.store.Update(func(st *State)error{for id,title:=range map[string]string{"b":"Echo","a":"echo","c":"Alpha"}{st.Tracks[id]=Track{ID:id,Title:title,Published:true,Audio:wave()};st.Albums[id]=Album{ID:id,Title:title,Published:true}};return nil});e!=nil{t.Fatal(e)}
 c:=newClient(t,a);for _,kind:=range []string{"tracks","albums"}{for n:=0;n<8;n++{
  p:=r1Get(c,"/api/catalog/"+kind+"?page_size=2");if !reflect.DeepEqual(r1IDs(p),[]string{"c","a"}){t.Fatal("ascending",r1IDs(p))}
  p=r1Get(c,"/api/catalog/"+kind+"?sort=-title&page_size=2");if !reflect.DeepEqual(r1IDs(p),[]string{"a","b"}){t.Fatal("descending ties",r1IDs(p))}
  p=r1Get(c,"/api/catalog/"+kind+"?page=2&page_size=2");if !reflect.DeepEqual(r1IDs(p),[]string{"b"}){t.Fatal("unstable boundary")}
 }}
}
func TestR1SearchAndFilteredTotals(t *testing.T) {
 a,admin,_:=environment(t);r1Seed(t,a);g:=newClient(t,a)
 for _,kind:=range []string{"tracks","albums"}{
  p:=r1Get(g,"/api/catalog/"+kind+"?q=%20sOnG%20&page_size=1");if p.Total!=12||len(p.Items)!=1{t.Fatal("case/whitespace search")}
  p=r1Get(g,"/api/catalog/"+kind+"?q=hidden");if p.Total!=0{t.Fatal("hidden content leaked into total")}
  p=r1Get(admin,"/api/admin/catalog/"+kind+"?q=HIDDEN&state=withdrawn&page_size=1");if p.Total!=1||p.Items[0].Status!="withdrawn"{t.Fatal("filtered total/state")}
  p=r1Get(admin,"/api/admin/catalog/"+kind+"?q=hidden&state=all");if p.Total!=2{t.Fatal("admin total")}
 }
 if p:=r1Get(g,"/api/catalog/albums?q=summer");p.Total!=12{t.Fatal("album description not searchable")}
 if p:=r1Get(g,"/api/catalog/tracks?q=summer");p.Total!=0{t.Fatal("track search used unrelated fields")}
}
func TestR1StrictCatalogInputsAndAuthorization(t *testing.T) {
 a,admin,_:=environment(t);r1Seed(t,a);g:=newClient(t,a);ordinary,_,_:=fan(t,a)
 bad:=[]string{"page=0","page=-1","page=1.5","page=x","page=","page=9223372036854775808","page_size=0","page_size=101","page_size=-1","page=1&page=2","sort=random","state=deleted","unknown=x","q=%FF","q=%zz","q="+strings.Repeat("x",201)}
 for _,kind:=range []string{"tracks","albums"}{
  for _,q:=range bad{g.expect(g.request("GET","/api/catalog/"+kind+"?"+q,nil,nil),400)}
  for _,c:=range []*client{g,ordinary,admin}{for _,state:=range []string{"all","draft","withdrawn"}{c.expect(c.request("GET","/api/catalog/"+kind+"?state="+state,nil,nil),403)}}
  for _,c:=range []*client{g,ordinary}{c.expect(c.request("GET","/api/admin/catalog/"+kind+"?state=all",nil,nil),403)}
  if r1Get(admin,"/api/admin/catalog/"+kind).Total!=14{t.Fatal("administrator all default")}
 }
}
func r1Media(c *client,path string,visible bool) {
 c.t.Helper();want:=404;if visible{want=200}
 for _,method:=range []string{"GET","HEAD"}{w:=c.request(method,path,nil,nil);c.expect(w,want);if w.Header().Get("Cache-Control")!="no-store"{c.t.Fatal("revoked media may be cached")}}
 want=404;if visible{want=206};c.expect(c.request("GET",path,nil,map[string]string{"Range":"bytes=0-7"}),want)
}
func TestR1TrackStatusLifecycleAndOldMediaURL(t *testing.T) {
 a,admin,_:=environment(t);id:=createTrack(admin,false);g:=newClient(t,a)
 for _,status:=range []string{"draft","published","withdrawn","draft","published"}{
  admin.post("/api/admin/tracks",map[string]any{"ID":id,"Title":"Lifecycle","Status":status},200)
  visible:=status=="published";want:=404;if visible{want=200};g.expect(g.request("GET","/api/tracks/"+id,nil,nil),want);r1Media(g,"/media/tracks/"+id,visible)
  count:=0;if visible{count=1};if r1Get(g,"/api/catalog/tracks").Total!=count||len(array(g.request("GET","/api/tracks",nil,nil)))!=count{t.Fatal("list/detail disagreement")}
  p:=r1Get(admin,"/api/admin/catalog/tracks?state="+status);if p.Total!=1||p.Items[0].Status!=status{t.Fatal("status filter")}
 }
 admin.post("/api/admin/tracks",map[string]any{"ID":id,"Title":"Legacy unpublish","Published":false},200)
 if r1Get(admin,"/api/admin/catalog/tracks?state=withdrawn").Total!=1{t.Fatal("legacy unpublish must record withdrawn")}
 admin.post("/api/admin/delete",map[string]string{"Kind":"track","ID":id},200);r1Media(g,"/media/tracks/"+id,false);g.expect(g.request("GET","/api/tracks/"+id,nil,nil),404)
 if r1Get(admin,"/api/admin/catalog/tracks").Total!=0{t.Fatal("deleted row still listed")}
}
func TestR1AlbumStatusControlsDetailAndEveryPhotoURL(t *testing.T) {
 a,admin,_:=environment(t);id:=createAlbum(admin,false);photo:=createPhoto(admin,id);g:=newClient(t,a)
 for _,status:=range []string{"draft","published","withdrawn","draft","published"}{
  admin.post("/api/admin/albums",map[string]any{"ID":id,"Title":"Lifecycle album","Description":"retained","Status":status},200)
  visible:=status=="published";want:=404;if visible{want=200};g.expect(g.request("GET","/api/albums/"+id,nil,nil),want);r1Media(g,"/media/photos/"+photo,visible)
  count:=0;if visible{count=1};if r1Get(g,"/api/catalog/albums").Total!=count{t.Fatal("album visibility")}
 }
 admin.post("/api/admin/delete",map[string]string{"Kind":"album","ID":id},200);r1Media(g,"/media/photos/"+photo,false);g.expect(g.request("GET","/api/albums/"+id,nil,nil),404)
 if r1Get(admin,"/api/admin/catalog/albums").Total!=0{t.Fatal("deleted album listed")}
}
func TestR1InvalidPublicationChangesAreAtomic(t *testing.T) {
 a,c,_:=environment(t);track:=createTrack(c,true);album:=createAlbum(c,true)
 for kind,id:=range map[string]string{"tracks":track,"albums":album}{for _,bad:=range []map[string]any{{"ID":id,"Title":"must not change","Status":"invalid"},{"ID":id,"Title":"must not change","Status":"draft","Published":true}}{
  before,e:=os.ReadFile(a.store.path);if e!=nil{t.Fatal(e)};c.post("/api/admin/"+kind,bad,400);after,_:=os.ReadFile(a.store.path);if !bytes.Equal(before,after){t.Fatal("rejected state request changed storage")}
 }}
}
func TestR1MigrateRealV1BytesAndRestartWithoutDataLoss(t *testing.T) {
 a,c,phrase:=environment(t);track:=createTrack(c,true);draft:=createTrack(c,false);album:=createAlbum(c,true);photo:=createPhoto(c,album)
 legacy:=a.store.Snapshot();legacy.Version=1
 for id,v:=range legacy.Tracks{v.Status="";legacy.Tracks[id]=v};for id,v:=range legacy.Albums{v.Status="";legacy.Albums[id]=v}
 raw,e:=json.Marshal(legacy);if e!=nil{t.Fatal(e)};if bytes.Contains(raw,[]byte(`"status"`)){t.Fatal("fixture is not v1")}
 dir:=t.TempDir();path:=filepath.Join(dir,"state.json");if e=os.WriteFile(path,raw,0600);e!=nil{t.Fatal(e)}
 migrated,e:=OpenStore(dir);if e!=nil{t.Fatal(e)};st:=migrated.Snapshot()
 if st.Version!=2||st.Tracks[track].Status!="published"||st.Tracks[draft].Status!="draft"||!reflect.DeepEqual(st.Users,legacy.Users)||!bytes.Equal(st.Tracks[track].Audio,legacy.Tracks[track].Audio)||!bytes.Equal(st.Photos[photo].Data,legacy.Photos[photo].Data){t.Fatal("migration data loss")}
 persisted,_:=os.ReadFile(path);if bytes.Equal(persisted,raw){t.Fatal("migration was not persisted")}
 reopened,e:=OpenStore(dir);if e!=nil{t.Fatal(e)};again,_:=os.ReadFile(path);if !bytes.Equal(persisted,again){t.Fatal("repeat migration changed state")}
 b:=NewApp(reopened,false);c.a=b;c.expect(c.request("GET","/api/me",nil,nil),403);login:=newClient(t,b);login.post("/api/login",map[string]string{"Email":"admin@example.invalid","Password":phrase},200)
 r1Media(login,"/media/tracks/"+track,true);r1Media(login,"/media/photos/"+photo,true);r1Media(login,"/media/tracks/"+draft,false)
}
func TestR1RestartKeepsFilteredOrderingAndWithdrawnURLs(t *testing.T) {
 a,admin,phrase:=environment(t);r1Seed(t,a);photo:=createPhoto(admin,"a-withdrawn");g:=newClient(t,a)
 paths:=[]string{"/api/catalog/tracks?q=SONG&page=2&page_size=5","/api/catalog/albums?q=summer&sort=-title&page=2&page_size=5"};before:=map[string]string{}
 for _,path:=range paths{w:=g.request("GET",path,nil,nil);g.expect(w,200);before[path]=w.Body.String()}
 management:=admin.request("GET","/api/admin/catalog/tracks?state=withdrawn",nil,nil).Body.String()
 store,e:=OpenStore(filepath.Dir(a.store.path));if e!=nil{t.Fatal(e)};b:=NewApp(store,false);g=newClient(t,b)
 for _,path:=range paths{w:=g.request("GET",path,nil,nil);g.expect(w,200);if w.Body.String()!=before[path]{t.Fatal("restart changed stable page")}}
 admin.a=b;admin.expect(admin.request("GET","/api/admin/catalog/tracks",nil,nil),403);admin=newClient(t,b);admin.post("/api/login",map[string]string{"Email":"admin@example.invalid","Password":phrase},200)
 if got:=admin.request("GET","/api/admin/catalog/tracks?state=withdrawn",nil,nil).Body.String();got!=management{t.Fatal("withdrawn state changed")}
 r1Media(g,"/media/tracks/t-withdrawn",false);r1Media(g,"/media/photos/"+photo,false);g.expect(g.request("GET","/api/albums/a-withdrawn",nil,nil),404)
}

var _ = http.StatusOK
