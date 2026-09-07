package main

import (
 "bytes"
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
 "sort"
 "strings"
 "sync"
 "time"
 "unicode/utf8"
 "golang.org/x/crypto/pbkdf2"
)

var errInput = errors.New("invalid input")
var errDenied = errors.New("not authorized")
var errNotFound = errors.New("not found")
var errConflict = errors.New("conflict")
const rounds = 600000

type User struct {
 ID string `json:"id"`
 Email string `json:"email"`
 Name string `json:"name"`
 Bio string `json:"bio"`
 Admin bool `json:"admin"`
 Enabled bool `json:"enabled"`
 SessionVersion uint64 `json:"session_version"`
 Salt string `json:"salt"`
 PasswordHash string `json:"password_hash"`
}
type Track struct { ID string; Title string; Published bool; Audio []byte }
type Photo struct { ID string; Caption string; ContentType string; Data []byte }
type Album struct { ID string; Title string; Description string; Published bool; Photos map[string]Photo }
type State struct { Version int; Title string; Intro string; Users map[string]User; Tracks map[string]Track; Albums map[string]Album }
type Store struct { mu sync.RWMutex; data State; path string; persist func([]byte) error }
func randomID() string { b:=make([]byte,32);if _,e:=rand.Read(b);e!=nil { panic(e) };return hex.EncodeToString(b) }
func cleanText(v string,max int) bool { return utf8.ValidString(v)&&utf8.RuneCountInString(v)<=max }
func emailKey(v string)(string,error) {
 v=strings.ToLower(strings.TrimSpace(v));a,e:=mail.ParseAddress(v)
 if e!=nil || a.Address!=v || len(v)>254 { return "",errInput };return v,nil
}
func hashPassword(phrase,salt string) string { return hex.EncodeToString(pbkdf2.Key([]byte(phrase),[]byte(salt),rounds,32,sha256.New)) }
func validPassword(phrase string) bool { return len(phrase)>=10&&len(phrase)<=72&&utf8.ValidString(phrase) }
func cloneState(s State) State { b,_:=json.Marshal(s);var n State;if e:=json.Unmarshal(b,&n);e!=nil { panic(e) };return n }
func OpenStore(dir string)(*Store,error) {
 if e:=os.MkdirAll(dir,0700);e!=nil{return nil,e}
 s:=&Store{path:filepath.Join(dir,"state.json"),data:State{Version:1,Title:"杨千嬅 · 粉丝小站",Intro:"非官方网站。音乐与图片为功能测试素材，不代表艺人录音或照片。",Users:map[string]User{},Tracks:map[string]Track{},Albums:map[string]Album{}}}
 if st,e:=os.Lstat(s.path);e==nil {
  if !st.Mode().IsRegular(){return nil,errInput};b,e:=os.ReadFile(s.path);if e!=nil{return nil,e}
  dec:=json.NewDecoder(bytes.NewReader(b));dec.DisallowUnknownFields();if e=dec.Decode(&s.data);e!=nil{return nil,e}
  if s.data.Version!=1||s.data.Users==nil||s.data.Tracks==nil||s.data.Albums==nil{return nil,errInput}
 }else if !os.IsNotExist(e){return nil,e}
 s.persist=func(b []byte) error {
  f,e:=os.CreateTemp(dir,".state-*");if e!=nil{return e};name:=f.Name();defer os.Remove(name)
  if _,e=f.Write(b);e!=nil{f.Close();return e};if e=f.Sync();e!=nil{f.Close();return e};if e=f.Close();e!=nil{return e}
  return os.Rename(name,s.path)
 }
 return s,nil
}
func(s *Store) Snapshot()State{s.mu.RLock();defer s.mu.RUnlock();return cloneState(s.data)}
func(s *Store) Update(fn func(*State)error)error {
 s.mu.Lock();defer s.mu.Unlock();next:=cloneState(s.data);if e:=fn(&next);e!=nil{return e}
 b,e:=json.Marshal(next);if e!=nil{return e};if e=s.persist(b);e!=nil{return fmt.Errorf("storage unavailable: %w",e)};s.data=next;return nil
}
func(s *Store) Register(email,phrase,name string,admin bool)(User,error) {
 email,e:=emailKey(email);if e!=nil||!validPassword(phrase)||!cleanText(name,80){return User{},errInput}
 u:=User{ID:randomID(),Email:email,Name:strings.TrimSpace(name),Admin:admin,Enabled:true,Salt:randomID()};u.PasswordHash=hashPassword(phrase,u.Salt)
 e=s.Update(func(st *State)error{for _,old:=range st.Users{if old.Email==email{return errConflict}};st.Users[u.ID]=u;return nil});return u,e
}
func(s *Store) Authenticate(email,phrase string)(User,error) {
 email,e:=emailKey(email);if e!=nil||!validPassword(phrase){return User{},errDenied}
 st:=s.Snapshot();for _,u:=range st.Users{if u.Email==email&&u.Enabled {
  h:=hashPassword(phrase,u.Salt);if subtle.ConstantTimeCompare([]byte(h),[]byte(u.PasswordHash))==1{return u,nil};break
 }};return User{},errDenied
}
func(s *Store) Bootstrap(email,phrase string)error {
 if email==""&&phrase==""{return nil};if email==""||phrase==""{return errInput}
 if len(s.Snapshot().Users)>0{return nil};_,e:=s.Register(email,phrase,"站点管理员",true);return e
}
func sortedKeys[T any](m map[string]T)[]string{v:=make([]string,0,len(m));for k:=range m{v=append(v,k)};sort.Strings(v);return v}
type Session struct { UserID string; Version uint64; CSRF string; Expires time.Time }
