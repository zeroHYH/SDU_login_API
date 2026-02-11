from dataclasses import dataclass
from datetime import datetime, timedelta
from random import random

from fastapi import Body, FastAPI, HTTPException, Request, Response
from fastapi.staticfiles import StaticFiles
from httpx import Client, HTTPError
from uvicorn import run

from uniform_login_des import strEnc

app = FastAPI(debug=True, title="统一认证短信登录")


@dataclass
class LoginSession:
    client: Client
    expire: datetime


login_sessions: dict[str, LoginSession] = {}


def clean_expired_sessions():
    now = datetime.now()
    expired = [c for c, ls in login_sessions.items() if now > ls.expire]
    for c in expired:
        login_sessions.pop(c)


@app.post("/code")
def get_image_code(request: Request):
    clean_expired_sessions()
    ls = request.cookies.get("login_session")
    new_session = False
    if not ls or ls not in login_sessions:
        ls = str(random())
        login_sessions[ls] = LoginSession(
            client=Client(), expire=datetime.now() + timedelta(minutes=2)
        )
        new_session = True
    try:
        upstream = login_sessions[ls].client.get(
            f"https://pass.sdu.edu.cn/cas/code?{ls}"
        )
    except HTTPError:
        raise HTTPException(503, "cas unavailable")
    media_type = upstream.headers.get("content-type", "image/gif")
    response = Response(upstream.content, media_type=media_type)
    if new_session:
        response.set_cookie("login_session", ls, max_age=150, httponly=True)
    return response


@app.post("/sms")
def get_sms_code(
    request: Request,
    response: Response,
    mobile: str = Body(max_length=11, min_length=11, pattern=r"^\d+$"),
    code: str = Body(max_length=4, min_length=4, pattern=r"^\d+$"),
):
    clean_expired_sessions()
    ls = request.cookies.get("login_session")
    if not ls or ls not in login_sessions:
        raise HTTPException(400, "Invalid session or session expired")
    try:
        url = (
            login_sessions[ls]
            .client.post(
                "https://pass.sdu.edu.cn/cas/loginByMorE",
                data={
                    "method": "sendMobileCode",
                    "sendConfirm": code,
                    "mobile": mobile,
                    "random": random(),
                },
            )
            .json()
            .get("redirectUrl")
        )
    except HTTPError:
        raise HTTPException(503, "cas unavailable")
    if url == "login":
        response.status_code = 201
    else:
        raise HTTPException(400, "Invalid code")


@app.post("/login")
def sms_login(
    request: Request,
    response: Response,
    mobile: str = Body(max_length=11, min_length=11, pattern=r"^\d+$"),
    code: str = Body(max_length=6, min_length=6, pattern=r"^\d+$"),
):
    clean_expired_sessions()
    ls = request.cookies.get("login_session")
    if not ls or ls not in login_sessions:
        raise HTTPException(400, "Invalid session or session expired")
    try:
        url = (
            login_sessions[ls]
            .client.post(
                "https://pass.sdu.edu.cn/cas/loginByMorE",
                data={
                    "method": "login",
                    "mobile": mobile,
                    "mobileCode": code,
                    "random": random(),
                    "service": "https://service.sdu.edu.cn/tp_up/view?m=up",
                },
            )
            .json()
            .get("redirectUrl")
        )
    except HTTPError:
        raise HTTPException(503, "cas unavailable")
    if not url:
        raise HTTPException(400, "Invalid code")
    try:
        login_sessions[ls].client.get(url, follow_redirects=True)
        sduid = (
            login_sessions[ls]
            .client.post(
                "https://service.sdu.edu.cn/tp_up/sys/uacm/profile/getUserType",
                json={},
                headers={
                    "Content-Type": "application/json;charset=UTF-8",
                },
            )
            .json()[0]["ID_NUMBER"]
        )
        info = (
            login_sessions[ls]
            .client.post(
                "https://service.sdu.edu.cn/tp_up/sys/uacm/profile/getUserById",
                json={"BE_OPT_ID": strEnc(sduid, "tp", "des", "param")},
                headers={
                    "Content-Type": "application/json;charset=UTF-8",
                },
            )
            .json()
        )
    except HTTPError:
        raise HTTPException(503, "could not get user info from service.sdu.edu.cn")
    login_sessions.pop(ls)
    response.delete_cookie("login_session")
    return {
        "name": info.get("USER_NAME"),
        "sduid": sduid,
        "email": info.get("EMAIL", ""),
    }


app.mount("/", StaticFiles(directory=".", html=True))


if __name__ == "__main__":
    run(app, port=8201)
