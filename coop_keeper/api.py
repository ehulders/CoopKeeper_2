import uvicorn
#import RPi.GPIO as GPIO

from .core import Location, CoopKeeper#, GPIOInit
from fastapi import FastAPI, Header, Request, Response
from pydantic import BaseModel


class App(FastAPI):
    app = FastAPI(
        title="CoopKeeper API",
        description="RestAPI for CoopKeeper",
        version="0.1a",
    )
    ck = CoopKeeper()


app = App()


def get_app():
    return app


@app.get("/door/{door_action}")
async def door(
        door_action: str,
        request: Request,
        response: Response,
    ):
    if door_action == 'open':
        if app.ck.door.present_mode() == "Auto":
            app.ck.door.hold_open_button()
        result = app.ck.door.push_open_button()
    elif door_action == 'close':
        if app.ck.door.present_mode() == "Auto":
            app.ck.door.hold_open_button()
        result = app.ck.door.push_close_button()
    elif door_action == 'auto':
        result = app.ck.door.hold_close_button()
    else:
        response.status_code = 400
        return {"result": "invalid action requested"}
    return {"result": result}


@app.get("/debug/{thing}")
async def debug(
        thing: str,
        request: Request,
        response: Response,
    ):
    if thing == 'time':
        result = {'current_time':
                  app.ck.coop_time.current_time,
                  'open_time':
                  app.ck.coop_time.open_time,
                  'close_time':
                  app.ck.coop_time.close_time}
    else:
        response.status_code = 400
        return {"result": "invalid thing requested"}
    return {"result": result}


def main():
    #uvicorn.run("start:app", host="0.0.0.0", port=5005, reload=True, log_level='info')
    get_app()
    #GPIO.output(GPIOInit.PIN_LED, GPIO.LOW)
    #app.ck.stop_door()