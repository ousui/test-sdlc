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

var errConflict = errors.New("account already exists")
var errInvalid = errors.New("invalid input")
var errMissing = errors.New("not found")
var errForbidden = errors.New("forbidden")

type User struct {
	ID             string `json:"id"`
	Email          string `json:"email"`
	Name           string `json:"name"`
	Bio            string `json:"bio"`
	PasswordHash   string `json:"password_hash"`
	Salt           string `json:"salt"`
	Admin          bool   `json:"admin"`
	Enabled        bool   `json:"enabled"`
	SessionVersion uint64 `json:"session_version"`
}
type Track struct {
	ID        string `json:"id"`
	Title     string `json:"title"`
	Audio     []byte `json:"audio"`
	Published bool   `json:"published"`
	Status    string `json:"status,omitempty"`
}
type Album struct {
	ID          string `json:"id"`
	Title       string `json:"title"`
	Description string `json:"description"`
	Published   bool   `json:"published"`
	Status      string `json:"status,omitempty"`
}
type Photo struct {
	ID      string `json:"id"`
	Album   string `json:"album"`
	Caption string `json:"caption"`
	Data    []byte `json:"data"`
}
type State struct {
	Version int              `json:"version"`
	Title   string           `json:"title"`
	Intro   string           `json:"intro"`
	Users   map[string]User  `json:"users"`
	Tracks  map[string]Track `json:"tracks"`
	Albums  map[string]Album `json:"albums"`
	Photos  map[string]Photo `json:"photos"`
}
type Store struct {
	mu      sync.RWMutex
	state   State
	path    string
	persist func([]byte) error
}

func randomID() string {
	b := make([]byte, 32)
	if _, err := rand.Read(b); err != nil {
		panic(err)
	}
	return hex.EncodeToString(b)
}
func cloneState(s State) State {
	b, err := json.Marshal(s)
	if err != nil {
		panic(err)
	}
	var copy State
	if err = json.Unmarshal(b, &copy); err != nil {
		panic(err)
	}
	return copy
}
func emptyState() State {
	return State{Version: 2, Title: "杨千嬅 · 非官方粉丝站", Intro: "分享喜爱，试听与图片均为自产演示。", Users: map[string]User{}, Tracks: map[string]Track{}, Albums: map[string]Album{}, Photos: map[string]Photo{}}
}
func OpenStore(dir string) (*Store, error) {
	if err := os.MkdirAll(dir, 0700); err != nil {
		return nil, err
	}
	s := &Store{path: filepath.Join(dir, "state.json"), state: emptyState()}
	s.persist = s.persistFile
	fi, err := os.Lstat(s.path)
	if err == nil {
		if !fi.Mode().IsRegular() {
			return nil, fmt.Errorf("state must be a regular file")
		}
		b, e := os.ReadFile(s.path)
		if e != nil {
			return nil, e
		}
		var existing State
		if e = json.Unmarshal(b, &existing); e != nil {
			return nil, e
		}
		// This FINAL R0 used schema_version; historical v1 fixtures used version.
		if existing.Version == 0 {
			var legacy struct {
				SchemaVersion int `json:"schema_version"`
			}
			if e = json.Unmarshal(b, &legacy); e != nil {
				return nil, e
			}
			existing.Version = legacy.SchemaVersion
		}
		if existing.Version != 1 && existing.Version != 2 || existing.Users == nil || existing.Tracks == nil || existing.Albums == nil || existing.Photos == nil {
			return nil, fmt.Errorf("invalid store schema")
		}
		changed, e := normalizePublication(&existing)
		if e != nil {
			return nil, e
		}
		if changed {
			upgraded, e := json.MarshalIndent(existing, "", "  ")
			if e != nil {
				return nil, e
			}
			if e = s.persist(upgraded); e != nil {
				return nil, e
			}
		}
		s.state = existing
	} else if !errors.Is(err, os.ErrNotExist) {
		return nil, err
	}
	return s, nil
}
func (s *Store) persistFile(b []byte) error {
	if fi, err := os.Lstat(s.path); err == nil && !fi.Mode().IsRegular() {
		return fmt.Errorf("state must be a regular file")
	} else if err != nil && !errors.Is(err, os.ErrNotExist) {
		return err
	}
	f, err := os.CreateTemp(filepath.Dir(s.path), ".state-*")
	if err != nil {
		return err
	}
	name := f.Name()
	defer os.Remove(name)
	if _, err = f.Write(b); err != nil {
		f.Close()
		return err
	}
	if err = f.Sync(); err != nil {
		f.Close()
		return err
	}
	if err = f.Close(); err != nil {
		return err
	}
	return os.Rename(name, s.path)
}
func (s *Store) Snapshot() State { s.mu.RLock(); defer s.mu.RUnlock(); return cloneState(s.state) }
func (s *Store) Update(fn func(*State) error) error {
	s.mu.Lock()
	defer s.mu.Unlock()
	next := cloneState(s.state)
	if err := fn(&next); err != nil {
		return err
	}
	if _, err := normalizePublication(&next); err != nil {
		return err
	}
	b, err := json.MarshalIndent(next, "", "  ")
	if err != nil {
		return err
	}
	if err = s.persist(b); err != nil {
		return err
	}
	s.state = next
	return nil
}
func cleanEmail(email string) (string, error) {
	email = strings.ToLower(strings.TrimSpace(email))
	a, err := mail.ParseAddress(email)
	if err != nil || a.Address != email || len(email) > 254 {
		return "", errInvalid
	}
	return email, nil
}
func validText(s string, max int) bool {
	return utf8.ValidString(s) && utf8.RuneCountInString(s) <= max
}
func (s *Store) Register(email, password, name string, admin bool) (User, error) {
	email, err := cleanEmail(email)
	if err != nil {
		return User{}, err
	}
	name = strings.TrimSpace(name)
	if name == "" {
		name = email
	}
	if len(password) < 12 || len(password) > 72 || !validText(name, 80) || name == "" {
		return User{}, errInvalid
	}
	salt := randomID()
	raw, _ := hex.DecodeString(salt)
	u := User{ID: randomID(), Email: email, Name: name, Salt: salt, PasswordHash: hex.EncodeToString(pbkdf2.Key([]byte(password), raw, 600000, 32, sha256.New)), Enabled: true, Admin: admin, SessionVersion: 1}
	err = s.Update(func(st *State) error {
		for _, old := range st.Users {
			if old.Email == email {
				return errConflict
			}
		}
		st.Users[u.ID] = u
		return nil
	})
	return u, err
}
func (s *Store) Bootstrap(email, password string) error {
	st := s.Snapshot()
	if len(st.Users) > 0 {
		return nil
	}
	_, err := s.Register(email, password, "Administrator", true)
	return err
}
func checkPassword(u User, password string) bool {
	if len(password) > 72 {
		return false
	}
	salt, err := hex.DecodeString(u.Salt)
	if err != nil {
		return false
	}
	expected, err := hex.DecodeString(u.PasswordHash)
	if err != nil {
		return false
	}
	got := pbkdf2.Key([]byte(password), salt, 600000, 32, sha256.New)
	return subtle.ConstantTimeCompare(expected, got) == 1
}

func publicationState(status string, published bool) (string, error) {
	if status == "" {
		if published {
			return "published", nil
		}
		return "draft", nil
	}
	switch status {
	case "draft", "published", "withdrawn":
		return status, nil
	}
	return "", errInvalid
}
func normalizePublication(st *State) (bool, error) {
	changed := st.Version != 2
	st.Version = 2
	for id, value := range st.Tracks {
		status, err := publicationState(value.Status, value.Published)
		if err != nil {
			return false, err
		}
		if value.Status != status || value.Published != (status == "published") {
			changed = true
		}
		value.Status = status
		value.Published = status == "published"
		st.Tracks[id] = value
	}
	for id, value := range st.Albums {
		status, err := publicationState(value.Status, value.Published)
		if err != nil {
			return false, err
		}
		if value.Status != status || value.Published != (status == "published") {
			changed = true
		}
		value.Status = status
		value.Published = status == "published"
		st.Albums[id] = value
	}
	return changed, nil
}
func requestedPublication(status *string, published *bool, previous string, creating bool) (string, error) {
	if status != nil {
		if *status == "" {
			return "", errInvalid
		}
		s, err := publicationState(*status, false)
		if err != nil {
			return "", err
		}
		if published != nil && *published != (s == "published") {
			return "", errInvalid
		}
		return s, nil
	}
	if published != nil {
		if *published {
			return "published", nil
		}
		if previous == "published" || previous == "withdrawn" {
			return "withdrawn", nil
		}
		return "draft", nil
	}
	if creating {
		return "draft", nil
	}
	return publicationState(previous, false)
}
