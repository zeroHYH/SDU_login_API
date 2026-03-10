from datetime import datetime
from random import random
from uuid import UUID, uuid7

import httpx
from fastapi import Body, FastAPI, HTTPException, Request, Response
from httpx import Client, Cookies, HTTPError
from pydantic import BaseModel, Field

from uniform_login_des import strEnc

app = FastAPI(debug=True, title="统一认证短信登录")


login_sessions: dict[str, Cookies] = {}


class SduerInfo(BaseModel):
    sduid: str = Field(validation_alias="ID_NUMBER", description="学号")
    name: str = Field(validation_alias="USER_NAME", description="姓名")
    sex: str = Field(validation_alias="USER_SEX", description="性别")
    type: str = Field(validation_alias="ID_TYPE", description="类型")
    email: str = Field(validation_alias="EMAIL", description="邮箱")
    school: str = Field(validation_alias="UNIT_NAME", description="学院")
    tel: str = Field(validation_alias="MOBILE", description="电话")


def clear_expired_sessions():
    now = datetime.now().timestamp()
    for u in [u for u in login_sessions if now > UUID(u).time + 120 * 1000]:
        login_sessions.pop(u)


@app.post("/code")
def get_image_code():
    clear_expired_sessions()
    try:
        upstream = httpx.get(f"https://pass.sdu.edu.cn/cas/code?{random()}")
    except HTTPError:
        raise HTTPException(503, "cas unavailable")
    login_sessions[(ls := uuid7().hex)] = upstream.cookies
    response = Response(upstream.content, media_type="image/gif")
    response.set_cookie("login_session", ls, max_age=120, httponly=True)
    return response


@app.post("/sms", status_code=201)
def get_sms_code(
    request: Request,
    mobile: str = Body(max_length=11, min_length=11, pattern=r"^\d+$"),
    code: str = Body(max_length=4, min_length=4, pattern=r"^\d+$"),
):
    clear_expired_sessions()
    if (ls := request.cookies.get("login_session")) not in login_sessions:
        raise HTTPException(400, "Invalid session or session expired")
    try:
        res = httpx.post(
            "https://pass.sdu.edu.cn/cas/loginByMorE",
            data={
                "method": "sendMobileCode",
                "sendConfirm": code,
                "mobile": mobile,
                "random": random(),
            },
            cookies=login_sessions[ls],
        )
    except HTTPError:
        raise HTTPException(503, "cas unavailable")
    login_sessions[ls].update(res.cookies)
    if error := res.json().get("error"):
        raise HTTPException(400, error)
    if res.json().get("redirectUrl") != "login":
        raise HTTPException(400, "Invalid code")


@app.post("/login", response_model=SduerInfo)
def sms_login(
    request: Request,
    mobile: str = Body(max_length=11, min_length=11, pattern=r"^\d+$"),
    code: str = Body(max_length=6, min_length=6, pattern=r"^\d+$"),
):
    clear_expired_sessions()
    if (ls := request.cookies.get("login_session")) not in login_sessions:
        raise HTTPException(400, "Invalid session or session expired")
    client = Client(cookies=login_sessions.pop(ls))
    try:
        res = client.post(
            "https://pass.sdu.edu.cn/cas/loginByMorE",
            data={
                "method": "login",
                "mobile": mobile,
                "mobileCode": code,
                "random": random(),
                "service": "https://service.sdu.edu.cn/tp_up/view?m=up",
            },
        )
    except HTTPError:
        raise HTTPException(503, "cas unavailable")
    if not (url := res.json().get("redirectUrl")):
        raise HTTPException(400, "Invalid code")
    try:
        client.get(url, follow_redirects=True)
        sduid = client.post(
            "https://service.sdu.edu.cn/tp_up/sys/uacm/profile/getUserType",
            json={},
            headers={
                "Content-Type": "application/json;charset=UTF-8",
            },
        ).json()[0]["ID_NUMBER"]
        info = client.post(
            "https://service.sdu.edu.cn/tp_up/sys/uacm/profile/getUserById",
            json={"BE_OPT_ID": strEnc(sduid, "tp", "des", "param")},
            headers={
                "Content-Type": "application/json;charset=UTF-8",
            },
        ).json()
    except HTTPError:
        raise HTTPException(503, "could not get user info from service.sdu.edu.cn")
    return info
