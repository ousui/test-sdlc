package main

import (
 "encoding/json"
 "os"
 "path/filepath"
 "testing"
)

func TestIndependentR2EmptyQ1StorePersistsSiteRevision(t *testing.T) {
 dir := t.TempDir()
 path := filepath.Join(dir, "state.json")
 legacy := []byte(`{"version":2,"title":"existing empty Q1 site","intro":"preserve me","users":{},"tracks":{},"albums":{},"photos":{}}`)
 if err := os.WriteFile(path, legacy, 0600); err != nil { t.Fatal(err) }
 s, err := OpenStore(dir); if err != nil { t.Fatal(err) }
 if s.Snapshot().SiteRevision != 1 { t.Fatal("missing in-memory revision 1") }
 raw, err := os.ReadFile(path); if err != nil { t.Fatal(err) }
 t.Logf("disk after OpenStore: %s", raw)
 var saved map[string]any
 if err := json.Unmarshal(raw, &saved); err != nil { t.Fatal(err) }
 if saved["site_revision"] != float64(1) { t.Fatalf("Q2 acceptance 1 requires missing revisions to be persisted: site_revision=%v", saved["site_revision"]) }
 if saved["title"] != "existing empty Q1 site" || saved["intro"] != "preserve me" { t.Fatal("site content changed") }
 reopened, err := OpenStore(dir); if err != nil { t.Fatal(err) }
 if reopened.Snapshot().SiteRevision != 1 { t.Fatal("revision lost after restart") }
}
