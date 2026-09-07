package main

import (
 "context"
 "log"
 "net/http"
 "os"
 "os/signal"
 "syscall"
 "time"
)
func main(){
 dir:=os.Getenv("FAN_DATA_DIR");if dir==""{dir="data"};store,e:=OpenStore(dir);if e!=nil{log.Fatal("cannot open local state")}
 if e=store.Bootstrap(os.Getenv("FAN_ADMIN_EMAIL"),os.Getenv("FAN_ADMIN_PASSWORD"));e!=nil{log.Fatal("invalid explicit administrator setup")}
 addr:=os.Getenv("FAN_ADDR");if addr==""{addr="127.0.0.1:8080"}
 app:=NewApp(store,os.Getenv("FAN_SECURE_COOKIE")=="true")
 srv:=&http.Server{Addr:addr,Handler:app,ReadHeaderTimeout:5*time.Second,ReadTimeout:15*time.Second,WriteTimeout:15*time.Second,IdleTimeout:30*time.Second,MaxHeaderBytes:16384}
 ctx,stop:=signal.NotifyContext(context.Background(),os.Interrupt,syscall.SIGTERM);defer stop()
 go func(){<-ctx.Done();c,cancel:=context.WithTimeout(context.Background(),5*time.Second);defer cancel();srv.Shutdown(c)}()
 log.Print("unofficial fan-site local server starting; see README for scope")
 if e=srv.ListenAndServe();e!=nil&&e!=http.ErrServerClosed{log.Fatal("HTTP server stopped unexpectedly")}
}
