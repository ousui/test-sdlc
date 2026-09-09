package main

import (
	"net/http"
	"net/url"
	"sort"
	"strconv"
	"strings"
	"unicode"
	"unicode/utf8"
)

// foldKey represents Unicode simple-case equivalence, including final sigma.
func foldKey(text string) string {
	var out strings.Builder
	for _, r := range text {
		small := r
		for next := unicode.SimpleFold(r); next != r; next = unicode.SimpleFold(next) {
			if next < small {
				small = next
			}
		}
		out.WriteRune(small)
	}
	return out.String()
}

type catalogQuery struct {
	query, state, order string
	page                int64
	size                int
}

func parseCatalog(raw string, admin bool) (catalogQuery, error) {
	q := catalogQuery{state: "published", order: "title", page: 1, size: 10}
	if admin {
		q.state = "all"
	}
	values, err := url.ParseQuery(raw)
	if err != nil {
		return q, errInvalid
	}
	for key, list := range values {
		if len(list) != 1 {
			return q, errInvalid
		}
		switch key {
		case "q", "state", "sort", "page", "page_size":
		default:
			return q, errInvalid
		}
		if !utf8.ValidString(list[0]) {
			return q, errInvalid
		}
	}
	if text, ok := values["q"]; ok {
		if !validText(text[0], 200) {
			return q, errInvalid
		}
		q.query = foldKey(strings.TrimSpace(text[0]))
	}
	if v, ok := values["state"]; ok {
		q.state = v[0]
	}
	switch q.state {
	case "all", "draft", "published", "withdrawn":
	default:
		return q, errInvalid
	}
	if !admin && q.state != "published" {
		return q, errForbidden
	}
	if v, ok := values["sort"]; ok {
		q.order = v[0]
	}
	if q.order != "title" && q.order != "-title" {
		return q, errInvalid
	}
	for _, name := range []string{"page", "page_size"} {
		if list, ok := values[name]; ok {
			v := list[0]
			if v == "" {
				return q, errInvalid
			}
			for _, digit := range v {
				if digit < '0' || digit > '9' {
					return q, errInvalid
				}
			}
			n, e := strconv.ParseInt(v, 10, 64)
			if e != nil || n < 1 {
				return q, errInvalid
			}
			if name == "page" {
				q.page = n
			} else {
				if n > 100 {
					return q, errInvalid
				}
				q.size = int(n)
			}
		}
	}
	return q, nil
}
func trackView(v Track) map[string]any {
	return map[string]any{"id": v.ID, "title": v.Title, "published": v.Status == "published", "status": v.Status, "url": "/media/tracks/" + v.ID}
}
func albumView(v Album) map[string]any {
	return map[string]any{"id": v.ID, "title": v.Title, "description": v.Description, "published": v.Status == "published", "status": v.Status}
}
func (a *App) catalog(w http.ResponseWriter, r *http.Request) {
	if r.Method != "GET" {
		w.WriteHeader(405)
		return
	}
	admin := strings.HasPrefix(r.URL.Path, "/api/admin/")
	if admin {
		u, ok := a.user(r)
		if !ok || !u.Admin {
			problem(w, errForbidden)
			return
		}
	}
	kind := strings.TrimPrefix(r.URL.Path, "/api/catalog/")
	if admin {
		kind = strings.TrimPrefix(r.URL.Path, "/api/admin/catalog/")
	}
	if kind != "tracks" && kind != "albums" {
		problem(w, errMissing)
		return
	}
	q, err := parseCatalog(r.URL.RawQuery, admin)
	if err != nil {
		problem(w, err)
		return
	}
	st := a.store.Snapshot()
	items := []map[string]any{}
	if kind == "tracks" {
		for _, v := range st.Tracks {
			if (q.state == "all" || q.state == v.Status) && strings.Contains(foldKey(v.Title), q.query) {
				items = append(items, trackView(v))
			}
		}
	} else {
		for _, v := range st.Albums {
			if (q.state == "all" || q.state == v.Status) && (strings.Contains(foldKey(v.Title), q.query) || strings.Contains(foldKey(v.Description), q.query)) {
				items = append(items, albumView(v))
			}
		}
	}
	sort.Slice(items, func(i, j int) bool {
		a, b := foldKey(items[i]["title"].(string)), foldKey(items[j]["title"].(string))
		if a == b {
			return items[i]["id"].(string) < items[j]["id"].(string)
		}
		if q.order == "-title" {
			return a > b
		}
		return a < b
	})
	total := len(items)
	pageItems := []map[string]any{}
	// Compare before multiplying: even MaxInt64 page is a valid empty page.
	if q.page <= int64((total+q.size-1)/q.size) {
		start := int(q.page-1) * q.size
		end := start + q.size
		if end > total {
			end = total
		}
		pageItems = items[start:end]
	}
	respond(w, 200, map[string]any{"items": pageItems, "total": total, "page": q.page, "page_size": q.size})
}
