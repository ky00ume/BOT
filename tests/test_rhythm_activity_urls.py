import os, asyncio
from player import Player
from music_system import learn_melody,equip_instrument,equip_score
from cogs.town_cog import InstrumentPerformanceSetupView

class Resp:
    def __init__(self): self.payload=None
    async def send_message(self,*args,**kwargs): self.payload=(args,kwargs)
class Inter:
    def __init__(self): self.response=Resp()

async def main():
    os.environ['RHYTHM_ACTIVITY_URLS']='https://a.example/rhythm.html,https://b.example/rhythm.html'
    os.environ.pop('RHYTHM_ACTIVITY_URL',None)
    p=Player(); learn_melody(p,'eight_shadows'); equip_instrument(p,'lute'); equip_score(p,'eight_shadows')
    v=InstrumentPerformanceSetupView(p); inter=Inter(); await v._start(inter)
    _args,kwargs=inter.response.payload
    urls=[getattr(x,'url',None) for x in kwargs['view'].children]
    assert urls==['https://a.example/rhythm.html?song=eight_shadows','https://b.example/rhythm.html?song=eight_shadows']
    print('MULTI_URL_OK',urls)

if __name__=='__main__': asyncio.run(main())
