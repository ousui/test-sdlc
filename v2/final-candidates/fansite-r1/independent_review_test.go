package main

import (
 "net/url"
 "strings"
 "testing"
)

func TestIndependentUnicodeCaseInsensitiveCatalogSearch(t *testing.T) {
 // Final sigma and ordinary sigma are a standard Unicode simple-case pair.
 if !strings.EqualFold("ΟΣ", "ος") { t.Fatal("invalid Unicode counterexample fixture") }
 a,admin,_:=environment(t)
 admin.post("/api/admin/tracks",map[string]any{"Title":"ΟΣ","Status":"published","Audio":wave()},200)
 admin.post("/api/admin/albums",map[string]any{"Title":"Greek description","Description":"ΟΣ","Status":"published"},200)
 guest:=newClient(t,a)
 for _,kind:=range []string{"tracks","albums"} {
  t.Run(kind,func(t *testing.T) {
   for _,scope:=range []struct{name,path string; c *client}{{"public","/api/catalog/",guest},{"admin","/api/admin/catalog/",admin}} {
    t.Run(scope.name,func(t *testing.T) {
     base:=scope.path+kind+"?state=published&q="
     upper:=r1Get(scope.c,base+url.QueryEscape("ΟΣ"))
     if upper.Total!=1 {t.Fatalf("exact upper-case search fixture did not match: %+v",upper)}
     lower:=r1Get(scope.c,base+url.QueryEscape("ος"))
     if lower.Total!=1||len(lower.Items)!=1 {t.Errorf("Unicode case-equivalent query lost published result: %+v",lower)}
    })
   }
  })
 }
}
