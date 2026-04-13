"""renderer/singleton.py — get_renderer() + render_async() 싱글톤"""
import io
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

from renderer.cards import BG3Renderer

# ══════════════════════════════════════════════════════════════════
# 싱글톤 (스레드 안전)
# ══════════════════════════════════════════════════════════════════
_renderer: Optional[BG3Renderer] = None
_renderer_lock = threading.Lock()


def get_renderer() -> BG3Renderer:
    global _renderer
    if _renderer is None:
        with _renderer_lock:
            if _renderer is None:
                _renderer = BG3Renderer()
    return _renderer


# ══════════════════════════════════════════════════════════════════
# 비동기 래퍼 (이벤트 루프 블로킹 방지)
# ══════════════════════════════════════════════════════════════════
_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="bg3_render")


async def render_async(func, *args, **kwargs) -> io.BytesIO:
    """
    PIL 렌더링을 ThreadPoolExecutor에서 실행하여
    Discord 봇의 asyncio 이벤트 루프를 블로킹하지 않는다.

    사용 예:
        from bg3_renderer import get_renderer, render_async
        r = get_renderer()
        buf = await render_async(r.render_card, title="...", rows=[...])
        await ctx.send(file=discord.File(fp=buf, filename="card.png"))
    """
    import asyncio
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(_executor, lambda: func(*args, **kwargs))
