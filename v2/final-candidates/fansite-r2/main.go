package main

import (
	"log"
	"net/http"
	"os"
	"time"
)

func main() {
	dir := os.Getenv("FAN_DATA_DIR")
	if dir == "" {
		dir = "data"
	}
	store, err := OpenStore(dir)
	if err != nil {
		log.Fatal(err)
	}
	if len(store.Snapshot().Users) == 0 {
		email := os.Getenv("FAN_ADMIN_EMAIL")
		password := os.Getenv("FAN_ADMIN_PASSWORD")
		if email == "" || password == "" {
			log.Fatal("set FAN_ADMIN_EMAIL and FAN_ADMIN_PASSWORD for first start")
		}
		if err = store.Bootstrap(email, password); err != nil {
			log.Fatal("cannot initialize administrator: ", err)
		}
	}
	addr := os.Getenv("FAN_ADDR")
	if addr == "" {
		addr = "127.0.0.1:8080"
	}
	server := &http.Server{Addr: addr, Handler: NewApp(store, os.Getenv("FAN_SECURE_COOKIE") == "1"), ReadHeaderTimeout: 5 * time.Second, ReadTimeout: 20 * time.Second, WriteTimeout: 20 * time.Second, IdleTimeout: 60 * time.Second, MaxHeaderBytes: 32 << 10}
	log.Printf("非官方粉丝站 listening at %s", addr)
	log.Fatal(server.ListenAndServe())
}
