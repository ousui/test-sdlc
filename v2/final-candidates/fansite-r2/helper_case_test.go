package main

import "testing"

func TestHelperPreservesExplicitVersionCasing(t *testing.T) {
	_, c, _ := environment(t)
	track := createTrack(c, true)
	r2Raw(c, "/api/admin/tracks", r2Body("tracks", track, 1), 200)
	album := createAlbum(c, true)
	createPhoto(c, album)
	for _, name := range []string{"Version", "VERSION", "version", "vErSiOn"} {
		for _, value := range []any{uint64(1), nil} {
			expected := 409
			if value == nil {
				expected = 428
			}
			c.post("/api/admin/tracks", map[string]any{"ID": track, "Title": "must not overwrite", name: value}, expected)
			if r2Revision(c, "tracks", track) != 2 {
				t.Fatal("explicit rejected version mutated track")
			}
		}
	}
	for _, name := range []string{"AlbumVersion", "ALBUMVERSION", "albumversion", "aLbUmVeRsIoN"} {
		for _, value := range []any{uint64(1), nil} {
			expected := 409
			if value == nil {
				expected = 428
			}
			c.post("/api/admin/photos", map[string]any{"Album": album, "Caption": "must not add", "Data": picture(), name: value}, expected)
			if r2Revision(c, "albums", album) != 2 {
				t.Fatal("explicit rejected album version mutated membership")
			}
		}
	}
}
