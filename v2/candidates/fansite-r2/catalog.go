package main

import (
 "net/http"
 "net/url"
 "sort"
 "strconv"
 "strings"
 "unicode"
)

type catalogQuery struct { Search, Sort, State string; Page, PageSize int }
type catalogItem struct {
 ID string `json:"id"`
 Revision uint64 `json:"revision"`
 Title string `json:"title"`
 Description string `json:"description,omitempty"`
 Published bool `json:"published"`
 Status string `json:"status"`
 URL string `json:"url,omitempty"`
}
type catalogPage struct { Items []catalogItem `json:"items"`; Total int `json:"total"`; Page int `json:"page"`; PageSize int `json:"page_size"` }

// catalogFold gives every Unicode simple-case equivalence class one stable key.
// ToLower alone does not merge final sigma with sigma or long s with s.
func catalogFold(value string) string {
 return strings.Map(func(r rune) rune {
  representative := r
  for next := unicode.SimpleFold(r); next != r; next = unicode.SimpleFold(next) {
   if next < representative { representative = next }
  }
  return unicode.ToLower(representative)
 }, value)
}

func parseCatalogQuery(raw string, admin bool) (catalogQuery, error) {
 q := catalogQuery{Sort:"title", State:"published", Page:1, PageSize:10}
 if admin { q.State = "all" }
 values, err := url.ParseQuery(raw); if err != nil { return q, errInvalid }
 for key, entries := range values {
  if len(entries) != 1 { return q, errInvalid }
  value := entries[0]
  switch key {
  case "q":
   if !validText(value, 200, false) { return q, errInvalid }
   q.Search = catalogFold(strings.TrimSpace(value))
  case "sort":
   if value != "title" && value != "-title" { return q, errInvalid }; q.Sort = value
  case "state":
   if value != "all" && value != "draft" && value != "published" && value != "withdrawn" { return q, errInvalid }
   q.State = value
  case "page", "page_size":
   number, e := strconv.Atoi(value); if e != nil || number < 1 { return q, errInvalid }
   if key == "page" { q.Page = number } else { if number > 100 { return q, errInvalid }; q.PageSize = number }
  default: return q, errInvalid
  }
 }
 if !admin && q.State != "published" { return q, errForbidden }
 return q, nil
}
func queryCatalog(st State, kind string, q catalogQuery) catalogPage {
 rows := make([]catalogItem, 0)
 accept := func(item catalogItem) {
  if q.State != "all" && item.Status != q.State { return }
  text := item.Title
  if kind == "albums" { text += " " + item.Description }
  if !strings.Contains(catalogFold(text), q.Search) { return }
  rows = append(rows, item)
 }
 if kind == "tracks" {
  for _, track := range st.Tracks { accept(catalogItem{ID:track.ID, Revision:track.Revision, Title:track.Title, Published:track.Published, Status:track.Status, URL:"/media/tracks/"+track.ID}) }
 } else {
  for _, album := range st.Albums { accept(catalogItem{ID:album.ID, Revision:album.Revision, Title:album.Title, Description:album.Description, Published:album.Published, Status:album.Status}) }
 }
 sort.Slice(rows, func(i,j int) bool {
  left, right := catalogFold(rows[i].Title), catalogFold(rows[j].Title)
  if left == right { return rows[i].ID < rows[j].ID }
  if q.Sort == "-title" { return left > right }; return left < right
 })
 result := catalogPage{Items:make([]catalogItem,0), Total:len(rows), Page:q.Page, PageSize:q.PageSize}
 // Compare before multiplication so an arbitrarily large valid page cannot overflow.
 if q.Page-1 > len(rows)/q.PageSize { return result }
 start := (q.Page-1)*q.PageSize
 if start >= len(rows) { return result }
 end := start + q.PageSize; if end > len(rows) { end = len(rows) }
 result.Items = rows[start:end]; return result
}
func serveCatalog(w http.ResponseWriter, r *http.Request, st State, kind string, admin bool) {
 q, err := parseCatalogQuery(r.URL.RawQuery, admin)
 if err != nil { resultError(w, err); return }
 output(w, http.StatusOK, queryCatalog(st, kind, q))
}
