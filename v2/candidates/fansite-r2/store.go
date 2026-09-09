package main

import (
 "crypto/rand"
 "crypto/sha256"
 "crypto/subtle"
 "encoding/hex"
 "encoding/json"
 "errors"
 "fmt"
 "net/mail"
 "os"
 "path/filepath"
 "strings"
 "sync"
 "unicode/utf8"

 "golang.org/x/crypto/pbkdf2"
)

var errConflict = errors.New("record already exists")
var errVersionRequired = errors.New("content version required")
var errStaleVersion = errors.New("content version conflict")
var errVersionExhausted = errors.New("content version exhausted")
const maxContentRevision uint64 = 9007199254740991

var errInvalid = errors.New("invalid input")
var errNotFound = errors.New("record not found")
var errForbidden = errors.New("operation forbidden")
var errBootstrapComplete = errors.New("bootstrap already complete")

type User struct {
 ID string `json:"id"`
 Email string `json:"email"`
 Name string `json:"name"`
 Bio string `json:"bio"`
 PasswordHash string `json:"password_hash"`
 Salt string `json:"salt"`
 Admin bool `json:"admin"`
 Enabled bool `json:"enabled"`
 SessionVersion uint64 `json:"session_version"`
}
type Track struct {
 ID string `json:"id"`
 Revision uint64 `json:"revision"`
 Title string `json:"title"`
 Published bool `json:"published"`
 Status string `json:"status,omitempty"`
 Audio []byte `json:"audio"`
}
type Album struct {
 ID string `json:"id"`
 Revision uint64 `json:"revision"`
 Title string `json:"title"`
 Description string `json:"description"`
 Published bool `json:"published"`
 Status string `json:"status,omitempty"`
}
type Photo struct {
 ID string `json:"id"`
 Revision uint64 `json:"revision"`
 Album string `json:"album"`
 Caption string `json:"caption"`
 Data []byte `json:"data"`
}
type State struct {
 Version int `json:"version"`
 SiteRevision uint64 `json:"site_revision"`
 Title string `json:"title"`
 Intro string `json:"intro"`
 Users map[string]User `json:"users"`
 Tracks map[string]Track `json:"tracks"`
 Albums map[string]Album `json:"albums"`
 Photos map[string]Photo `json:"photos"`
}
type Store struct {
 mu sync.Mutex
 path string
 state State
 persist func([]byte) error
}

func randomID() string {
 var raw [32]byte
 if _, err := rand.Read(raw[:]); err != nil { panic("operating system random source unavailable") }
 return hex.EncodeToString(raw[:])
}
func cloneState(in State) State {
 raw, err := json.Marshal(in); if err != nil { panic(err) }
 var out State
 if err := json.Unmarshal(raw, &out); err != nil { panic(err) }
 return out
}
func validateState(st State) error {
 if st.SiteRevision < 1 || st.SiteRevision > maxContentRevision || st.Version != 2 || st.Users == nil || st.Tracks == nil || st.Albums == nil || st.Photos == nil { return fmt.Errorf("invalid stored schema") }
 emails := map[string]bool{}
 for id, u := range st.Users {
  if id != u.ID || id == "" || u.Email == "" || emails[u.Email] || len(u.PasswordHash) != 64 || len(u.Salt) != 64 { return fmt.Errorf("invalid stored account") }
  emails[u.Email] = true
 }
 for id, v := range st.Tracks { if v.Revision < 1 || v.Revision > maxContentRevision || id == "" || id != v.ID || !validPublication(v.Status, v.Published) { return fmt.Errorf("invalid stored track") } }
 for id, v := range st.Albums { if v.Revision < 1 || v.Revision > maxContentRevision || id == "" || id != v.ID || !validPublication(v.Status, v.Published) { return fmt.Errorf("invalid stored album") } }
 for id, v := range st.Photos { if v.Revision < 1 || v.Revision > maxContentRevision || id == "" || id != v.ID { return fmt.Errorf("invalid stored photo") }; if _, ok := st.Albums[v.Album]; !ok { return fmt.Errorf("orphan stored photo") } }
 return nil
}
func OpenStore(dir string) (*Store, error) {
 if err := os.MkdirAll(dir, 0700); err != nil { return nil, err }
 path := filepath.Join(dir, "state.json")
 s := &Store{path:path, state:State{Version:2, SiteRevision:1, Title:"杨千嬅 · 非官方粉丝站", Intro:"音乐与记忆，因喜爱而相聚。", Users:map[string]User{}, Tracks:map[string]Track{}, Albums:map[string]Album{}, Photos:map[string]Photo{}}}
 migrated := false
 info, err := os.Lstat(path)
 if err == nil {
  if !info.Mode().IsRegular() { return nil, fmt.Errorf("state must be a regular file") }
  raw, e := os.ReadFile(path); if e != nil { return nil, e }
  // Decode existing data without new-store defaults so omitted revision fields migrate durably.
  s.state = State{}
  if e = json.Unmarshal(raw, &s.state); e != nil { return nil, fmt.Errorf("corrupt state: %w", e) }
  if s.state.Version == 1 {
   for id, v := range s.state.Tracks { v.Status = legacyPublication(v.Published); s.state.Tracks[id] = v }
   for id, v := range s.state.Albums { v.Status = legacyPublication(v.Published); s.state.Albums[id] = v }
   s.state.Version = 2; migrated = true
  }
  if normalizeContentRevisions(&s.state) { migrated = true }
  if e = validateState(s.state); e != nil { return nil, e }
 } else if !errors.Is(err, os.ErrNotExist) { return nil, err }
 s.persist = func(raw []byte) error {
  if info, e := os.Lstat(path); e == nil && !info.Mode().IsRegular() { return fmt.Errorf("state must be a regular file") } else if e != nil && !errors.Is(e, os.ErrNotExist) { return e }
  f, e := os.CreateTemp(dir, ".state-*"); if e != nil { return e }
  name := f.Name()
  defer os.Remove(name)
  if e = f.Chmod(0600); e == nil { _, e = f.Write(raw) }
  if e == nil { e = f.Sync() }
  closeErr := f.Close(); if e == nil { e = closeErr }; if e != nil { return e }
  return os.Rename(name, path)
 }
 if errors.Is(err, os.ErrNotExist) || migrated { raw, _ := json.Marshal(s.state); if e := s.persist(raw); e != nil { return nil, e } }
 return s, nil
}
func (s *Store) Snapshot() State { s.mu.Lock(); defer s.mu.Unlock(); return cloneState(s.state) }
func (s *Store) Update(fn func(*State) error) error {
 s.mu.Lock(); defer s.mu.Unlock()
 next := cloneState(s.state)
 if err := fn(&next); err != nil { return err }
 normalizeNewContent(&next)
 if err := validateState(next); err != nil { return err }
 raw, err := json.Marshal(next); if err != nil { return err }
 if err := s.persist(raw); err != nil { return err }
 s.state = cloneState(next)
 return nil
}
func accountInput(email, password, name string) (string, error) {
 email = strings.ToLower(strings.TrimSpace(email))
 parsed, err := mail.ParseAddress(email)
 if err != nil || parsed.Address != email || len(email) > 254 || len(password) < 10 || len(password) > 72 || utf8.RuneCountInString(name) > 80 { return "", errInvalid }
 return email, nil
}
func makeUser(email, password, name string, admin bool) User {
 salt := randomID()
 rawSalt, _ := hex.DecodeString(salt)
 hash := pbkdf2.Key([]byte(password), rawSalt, 600000, 32, sha256.New)
 return User{ID:randomID(), Email:email, Name:name, Admin:admin, Enabled:true, Salt:salt, PasswordHash:hex.EncodeToString(hash), SessionVersion:1}
}
func (s *Store) Register(email, password, name string, admin bool) (User, error) {
 normalized, err := accountInput(email, password, name); if err != nil { return User{}, err }
 user := makeUser(normalized, password, name, admin)
 err = s.Update(func(st *State) error { for _, v := range st.Users { if v.Email == normalized { return errConflict } }; st.Users[user.ID] = user; return nil })
 return user, err
}
func (s *Store) Bootstrap(email, password string) error {
 if len(s.Snapshot().Users) > 0 { return nil }
 normalized, err := accountInput(email, password, "管理员"); if err != nil { return err }
 user := makeUser(normalized, password, "管理员", true)
 err = s.Update(func(st *State) error { if len(st.Users) > 0 { return errBootstrapComplete }; st.Users[user.ID] = user; return nil })
 if errors.Is(err, errBootstrapComplete) { return nil }; return err
}
func (s *Store) Authenticate(email, password string) (User, error) {
 email = strings.ToLower(strings.TrimSpace(email))
 if len(password) > 72 || len(password) < 10 { return User{}, errForbidden }
 for _, user := range s.Snapshot().Users {
  if user.Email != email { continue }
  salt, err := hex.DecodeString(user.Salt); if err != nil { return User{}, errForbidden }
  hash := hex.EncodeToString(pbkdf2.Key([]byte(password), salt, 600000, 32, sha256.New))
  if subtle.ConstantTimeCompare([]byte(hash), []byte(user.PasswordHash)) != 1 || !user.Enabled { return User{}, errForbidden }
  return user, nil
 }
 return User{}, errForbidden
}

// Published remains the R0 compatibility field; status distinguishes drafts from withdrawals.
func legacyPublication(published bool) string {
 if published { return "published" }; return "draft"
}
func validPublication(status string, published bool) bool {
 return (status == "draft" || status == "published" || status == "withdrawn") && published == (status == "published")
}
func visibleContent(published bool, status string) bool { return published && status == "published" }
func normalizeNewContent(st *State) {
 normalizeContentRevisions(st)
 for id, v := range st.Tracks { if v.Status == "" { v.Status = legacyPublication(v.Published); st.Tracks[id] = v } }
 for id, v := range st.Albums { if v.Status == "" { v.Status = legacyPublication(v.Published); st.Albums[id] = v } }
}
func publicationTransition(old string, published *bool, requested *string) (string, error) {
 if old == "" { old = "draft" }
 if requested != nil {
  value := *requested
  if value != "draft" && value != "published" && value != "withdrawn" { return "", errInvalid }
  if published != nil && *published != (value == "published") { return "", errInvalid }
  return value, nil
 }
 if published != nil {
  if *published { return "published", nil }
  if old == "published" || old == "withdrawn" { return "withdrawn", nil }
  return "draft", nil
 }
 return old, nil
}

// Version comparison and the corresponding increment occur inside Store.Update.
func requireVersion(expected *uint64, current uint64) error {
 if expected == nil { return errVersionRequired }
 if *expected == 0 || *expected > maxContentRevision { return errInvalid }
 if *expected != current { return errStaleVersion }
 if current >= maxContentRevision { return errVersionExhausted }
 return nil
}
func normalizeContentRevisions(st *State) bool {
 changed := false
 if st.SiteRevision == 0 { st.SiteRevision = 1; changed = true }
 for id, v := range st.Tracks { if v.Revision == 0 { v.Revision = 1; st.Tracks[id] = v; changed = true } }
 for id, v := range st.Albums { if v.Revision == 0 { v.Revision = 1; st.Albums[id] = v; changed = true } }
 for id, v := range st.Photos { if v.Revision == 0 { v.Revision = 1; st.Photos[id] = v; changed = true } }
 return changed
}
