import asyncio, os, json, html
from pathlib import Path
from datetime import datetime, timedelta, timezone
from telethon import TelegramClient
from telethon.utils import get_display_name

CHAT_ID='6340811092'
repo=Path(r'C:\Users\Admin\Documents\Playground\outputs\powerbank-market-report')
base=repo/'assets'/'telegram_refs_misha_today_2026-05-21'
base.mkdir(parents=True, exist_ok=True)
media_root=base/'media'
media_root.mkdir(exist_ok=True)
jsonl=base/'messages_misha_today.jsonl'
ENV_PATH=Path(r'C:\Users\Admin\Documents\!        WWW\SYSTEM STATUS\VOICE\config.env')
SESSION_COPY=str(base/'user_main_copy')
SRC_SESSION=Path(r'C:\Users\Admin\Documents\!        WWW\data\telegram_sessions\user_main.session')
if SRC_SESSION.exists():
    (base/'user_main_copy.session').write_bytes(SRC_SESSION.read_bytes())

def read_env(path):
    d={}
    if path.exists():
        for line in path.read_text(encoding='utf-8',errors='ignore').splitlines():
            if '=' in line and not line.strip().startswith('#'):
                k,v=line.split('=',1)
                d[k.strip()]=v.strip().strip('"').strip("'")
    return d

def kind_of(msg):
    if msg.photo: return 'photo'
    if msg.video: return 'video'
    if msg.voice: return 'voice'
    if msg.audio: return 'audio'
    if msg.document: return 'document'
    return 'none'

async def main():
    env=read_env(ENV_PATH)
    api_id=int(env.get('TELEGRAM_API_ID') or os.getenv('TELEGRAM_API_ID'))
    api_hash=(env.get('TELEGRAM_API_HASH') or os.getenv('TELEGRAM_API_HASH'))
    client=TelegramClient(SESSION_COPY, api_id, api_hash)
    await client.connect()
    if not await client.is_user_authorized():
        raise RuntimeError('session unauthorized')

    msk=timezone(timedelta(hours=3))
    day_start_utc=datetime(2026,5,21,0,0,0,tzinfo=msk).astimezone(timezone.utc)
    entity=await client.get_entity(int(CHAT_ID))

    rows=[]
    async for msg in client.iter_messages(entity, limit=1200):
        if not msg.date:
            continue
        dt=msg.date.astimezone(timezone.utc)
        if dt < day_start_utc:
            break
        sender=''
        if msg.sender is not None:
            sender=get_display_name(msg.sender) or ''
        if 'Миша Ломан' not in sender:
            continue
        k=kind_of(msg)
        rel=''
        if k!='none':
            sub=media_root/k
            sub.mkdir(parents=True, exist_ok=True)
            p=await client.download_media(msg, file=str(sub/f'msg_{msg.id}'))
            if p:
                rel=str(Path(p).resolve().relative_to(base.resolve())).replace('\\','/')
        rows.append({'id':msg.id,'date_utc':dt.isoformat(),'sender':sender,'text':(msg.message or '').strip(),'kind':k,'media':rel})

    rows.sort(key=lambda r:r['date_utc'])
    with jsonl.open('w',encoding='utf-8') as f:
        for r in rows:
            f.write(json.dumps(r,ensure_ascii=False)+'\n')

    cards=[]
    for r in rows:
        txt=html.escape(r['text'])
        md=''
        if r['media']:
            rel='assets/telegram_refs_misha_today_2026-05-21/'+r['media']
            ext=Path(r['media']).suffix.lower()
            if ext in ['.jpg','.jpeg','.png','.webp','.gif']:
                md=f"<img src='{rel}' alt='msg_{r['id']}' loading='lazy'/>"
            elif ext in ['.mp4','.webm','.mov','.m4v']:
                md=f"<video controls preload='metadata' src='{rel}'></video>"
            elif ext in ['.ogg','.mp3','.wav','.m4a']:
                md=f"<audio controls src='{rel}'></audio>"
        cards.append(f"<article class='card'><div class='head'><b>{html.escape(r['sender'])}</b><span>#{r['id']}</span></div><div class='meta'>{html.escape(r['date_utc'])} • {html.escape(r['kind'])}</div><div class='text'>{txt}</div>{md}</article>")

    content=''.join(cards) if cards else '<p>За сегодня от Миши сообщений с референсами не найдено.</p>'
    page=f"<!doctype html><html lang='ru'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Миша: референсы за 21.05.2026</title><style>body{{margin:0;font-family:Inter,Segoe UI,Arial,sans-serif;background:#0c111b;color:#e9eef9}}.wrap{{max-width:1200px;margin:0 auto;padding:24px}}.hero{{padding:20px;border:1px solid #2a3550;border-radius:14px;background:linear-gradient(135deg,#111b2d,#0f1420)}}h1{{margin:0 0 8px;font-size:34px}}.muted{{color:#a4b3cf}}.grid{{margin-top:18px;display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:14px}}.card{{background:#111827;border:1px solid #263247;border-radius:12px;padding:12px}}.head{{display:flex;justify-content:space-between;gap:8px;margin-bottom:6px}}.meta{{font-size:12px;color:#96a6c3;margin-bottom:8px}}.text{{font-size:14px;white-space:pre-wrap;line-height:1.45;margin-bottom:10px}}img,video{{width:100%;border-radius:8px;border:1px solid #2a3952;background:#000}}audio{{width:100%}}a{{color:#86d7ff}}</style></head><body><div class='wrap'><section class='hero'><h1>Референсы от Миши за сегодня</h1><div class='muted'>Чат 6340811092 • дата 21.05.2026 • сообщений: {len(rows)}</div><p><a href='index.html'>На главную</a></p></section><section class='grid'>{content}</section></div></body></html>"
    (repo/'telegram-refs-misha-today-2026-05-21.html').write_text(page,encoding='utf-8')
    (base/'meta.json').write_text(json.dumps({'chat_id':CHAT_ID,'count':len(rows),'generated_utc':datetime.now(timezone.utc).isoformat()},ensure_ascii=False,indent=2),encoding='utf-8')
    print('rows',len(rows))
    await client.disconnect()

if __name__=='__main__':
    asyncio.run(main())
