#!/usr/bin/env python3
# Embaralhador inteligente da Radio Bitcoin -> gera /tmp/radio_playlist.txt
# - cada "volta" toca todas as musicas antes de repetir (nao repete cedo)
# - nunca 2 versoes da mesma musica em sequencia
# - vinhetas/boletins/mercado espalhados entre as musicas
# - inclui as musicas novas do DistroKid (novas_distrokid/)
import json, os, random

MUSIC_CATS = {'Bitcoin','Reggae','Rock','Reggae/Dub','Missão Bitcoin','Conteudo Especial'}
NEW_DIR='novas_distrokid'
PASSES=6      # quantas voltas geradas por vez (loop fica longo antes de repetir a ordem)
K=4           # a cada K musicas entra 1 conteudo falado/vinheta
MIN_GAP=5     # distancia minima entre faixas do mesmo "grupo de versao"

GROUPS={
 'R38':['11 de Setembro BTC R38 Avisou','September 11 BTC R38 Warned','Girls on  BTC R38Avisou','Girls on BTC R38 Avisou'],
 'Salvacao':['Bitcoin Salvação','Bitcoin e Salvação','A Salvação é Individual'],
 'Higher':['itaiton records - Higher Meditation Riddim Preview','itaiton records - HigherMeditationRiddimPreview3_64kb'],
 'Autocustodia':['Autocustódia','Autocustódia Inoxidável'],
 'Revolucao':['Voz da Revolução','Wake up to the revolution,','Wake up to the revolution'],
 'Missao':['🎯 Missão Bitcoin — Ciudad del Este','Spot Missão Bitcoin — Ciudad del Este 19-20 set'],
 'Nueve':['Nueve Millas - Abbat','Nueve Millas - Ayer soñé con Rastafari','Nueve Millas - 01_Nueve_Millas_-_Rivers_of_DUBylon','Nueve Millas - 02_Nueve_Millas_-_Natty_DUB'],
}
t2g={}
for g,ts in GROUPS.items():
    for t in ts: t2g[t]=g

def load():
    tracks=json.load(open('tracks.json'))
    new=[]
    if os.path.isdir(NEW_DIR):
        for f in sorted(os.listdir(NEW_DIR)):
            if f.lower().endswith('.mp3'):
                new.append({'title':os.path.splitext(f)[0],'file':f'{NEW_DIR}/{f}','category':'Bitcoin'})
    music=[t for t in tracks if t.get('category') in MUSIC_CATS]
    spoken=[t for t in tracks if t.get('category') not in MUSIC_CATS]
    return music+new, spoken

def build():
    music, spoken = load()
    for i,m in enumerate(music): m['grp']=t2g.get(m['title'], f'solo{i}')
    music=[m for m in music if os.path.exists(m['file'])]
    spoken=[s for s in spoken if os.path.exists(s['file'])]
    recent=[]; seq=[]
    for _ in range(PASSES):
        pool=music[:]; random.shuffle(pool)
        while pool:
            pick=None
            for i,it in enumerate(pool):
                if it['grp'] not in recent[-MIN_GAP:]:
                    pick=i; break
            if pick is None: pick=0
            it=pool.pop(pick); seq.append(it); recent.append(it['grp'])
    sp=spoken[:]; random.shuffle(sp); final=[]; si=0
    for i,m in enumerate(seq):
        final.append(m)
        if (i+1)%K==0 and sp:
            final.append(sp[si%len(sp)]); si+=1
    return final, music, spoken

final, music, spoken = build()
with open('/tmp/radio_playlist.txt','w') as f:
    f.write('\n'.join(f"file '{it['file']}'" for it in final))
bad=sum(1 for a,b in zip(final,final[1:]) if a.get('grp') and a.get('grp')==b.get('grp') and not str(a.get('grp')).startswith('solo'))
print(f"Playlist: {len(final)} itens ({len(music)} musicas x{PASSES} voltas + {len(spoken)} falados) | versoes seguidas: {bad}")
