package main

import (
 "errors"
 "log"
 "net/http"
 "os"
 "time"
)
func main() {
 dir:=os.Getenv("FAN_DATA_DIR");if dir==""{dir="data"}
 store,err:=OpenStore(dir);if err!=nil{log.Fatal("cannot open local state: ",err)}
 email,password:=os.Getenv("FAN_ADMIN_EMAIL"),os.Getenv("FAN_ADMIN_PASSWORD")
 if email!=""||password!=""{if email==""||password==""{log.Fatal("provide both administrator environment variables")};if err=store.Bootstrap(email,password);err!=nil{log.Fatal("administrator bootstrap failed")}}
 addr:=os.Getenv("FAN_ADDR");if addr==""{addr="127.0.0.1:8080"}
 server:=&http.Server{Addr:addr,Handler:NewApp(store,os.Getenv("FAN_SECURE_COOKIE")=="true"),ReadHeaderTimeout:5*time.Second,ReadTimeout:20*time.Second,WriteTimeout:30*time.Second,IdleTimeout:60*time.Second,MaxHeaderBytes:16<<10}
 log.Print("Unofficial fan site listening on ",addr)
 if err=server.ListenAndServe();err!=nil&&!errors.Is(err,http.ErrServerClosed){log.Fatal(err)}
}
