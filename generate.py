import json,re,subprocess,sys,time
from pathlib import Path
from datetime import datetime,timezone
CHANNELS=Path("channels.txt"); OUTPUT=Path("youtube_bd.m3u")
CLIENTS=["default,web_safari","android,ios"]

def run(cmd):
    for attempt in range(2):
        try:
            p=subprocess.run(cmd,capture_output=True,text=True,encoding="utf-8",errors="replace",timeout=150)
            if p.returncode==0:return p.stdout.strip(),""
            err=p.stderr.strip() or p.stdout.strip()
        except Exception as e:err=str(e)
        if attempt==0:time.sleep(2)
    return "","".join(err)

def load():
    out=[]
    for x in CHANNELS.read_text(encoding="utf-8").splitlines():
        if x.strip() and not x.lstrip().startswith("#") and "|" in x:
            n,u=x.split("|",1);out.append((n.strip(),u.strip()))
    return out

def discover(url):
    cmd=[sys.executable,"-m","yt_dlp","--dump-single-json","--flat-playlist","--playlist-end","8","--no-warnings","--quiet","--skip-download",url.rstrip("/")+"/live"]
    s,e=run(cmd)
    if not s:return [],e
    try:o=json.loads(s)
    except:return [],"invalid JSON"
    ids=[]
    if re.fullmatch(r"[\w-]{11}",str(o.get("id",""))):ids.append(o["id"])
    for z in o.get("entries") or []:
        v=(z or {}).get("id")
        if v and re.fullmatch(r"[\w-]{11}",v) and v not in ids:ids.append(v)
    return ids[:8],""

def info(vid,client):
    cmd=[sys.executable,"-m","yt_dlp","--dump-single-json","--no-playlist","--no-warnings","--quiet","--skip-download","--socket-timeout","60","--extractor-args",f"youtube:player_client={client}",f"https://www.youtube.com/watch?v={vid}"]
    s,e=run(cmd)
    if not s:return None,e
    try:return json.loads(s),""
    except:return None,"invalid JSON"

def hls(o):
    u=o.get("hlsManifestUrl")
    if u and ".m3u8" in u:return u,o.get("height") or 0
    a=[]
    for f in o.get("formats") or []:
        u=f.get("url") or "";m=f.get("manifest_url") or "";p=(f.get("protocol") or "").lower()
        if u and (".m3u8" in u or ".m3u8" in m or p.startswith("m3u8")):a.append(f)
    if not a:return None,0
    f=max(a,key=lambda x:(x.get("vcodec") not in (None,"none"),x.get("acodec") not in (None,"none"),x.get("height") or 0,x.get("fps") or 0,x.get("tbr") or 0))
    return f["url"],f.get("height") or 0

def resolve(name,url):
    print("\n["+name+"]")
    ids,err=discover(url)
    if not ids:return None,"discovery: "+err[:200]
    for vid in ids:
        for c in CLIENTS:
            o,e=info(vid,c)
            if not o:continue
            if o.get("live_status") not in ("is_live","live") and o.get("is_live") is not True:continue
            u,h=hls(o)
            if u:
                print(f" LIVE {vid} -> HLS {h or '?'}p")
                return {"name":name,"id":o.get("channel_id",""),"url":u,"height":h},""
    return None,"live found but no HLS"

def main():
    good=[];bad=[]
    for n,u in load():
        r,e=resolve(n,u)
        (good if r else bad).append(r or (n,e))
    lines=["#EXTM3U","#EXT-X-VERSION:3",f"# Updated: {datetime.now(timezone.utc):%Y-%m-%d %H:%M:%S UTC}",f"# Live channels: {len(good)}",""]
    for r in good:
        lines += [f'#EXTINF:-1 tvg-id="{r["id"]}" tvg-name="{r["name"]}" group-title="Bangladesh YouTube",{r["name"]} [{r["height"] or "HLS"}p]',r["url"],""]
    OUTPUT.write_text("\n".join(lines),encoding="utf-8")
    print(f"\nGenerated {OUTPUT}: {len(good)} live HLS channels")
    for n,e in bad:print("FAILED:",n,"-",e)

if __name__=="__main__":main()
