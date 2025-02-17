# @Time    : 2023/8/9 23:23
# @Author  : Lan
# @File    : main.py
# @Software: PyCharm
import asyncio
import os

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import HTMLResponse
from starlette.staticfiles import StaticFiles
from tortoise.contrib.fastapi import register_tortoise

from apps.base.views import share_api
from apps.admin.views import admin_api
from core.settings import data_root, settings
from core.tasks import delete_expire_files

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount('/assets', StaticFiles(directory='./fcb-fronted/dist/assets'), name="assets")

register_tortoise(
    app,
    generate_schemas=True,
    add_exception_handlers=True,
    config={
        'connections': {
            'default': f'sqlite://{data_root}/filecodebox.db'
        },
        'apps': {
            'models': {
                "models": ["apps.base.models"],
                'default_connection': 'default',
            }
        },
        "use_tz": False,
        "timezone": "Asia/Shanghai",
    }
)

app.include_router(share_api)
app.include_router(admin_api)


@app.on_event("startup")
async def startup_event():
    # 启动后台任务，不定时删除过期文件
    asyncio.create_task(delete_expire_files())


@app.get('/')
async def index():
    return HTMLResponse(
        content=open('./fcb-fronted/dist/index.html', 'r', encoding='utf-8').read()
        .replace('{{title}}', settings.name)
        .replace('{{description}}', settings.description)
        .replace('{{keywords}}', settings.keywords)
        .replace('{{opacity}}', settings.opacity)
        .replace('{{background}}', settings.background)
        , media_type='text/html', headers={'Cache-Control': 'no-cache'})


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app='main:app', host="0.0.0.0", port=settings.port, reload=False, workers=1)
