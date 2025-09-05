from requests import Session
from datetime import datetime, timezone
from re import search


def login(
    sduid: str,
    password: str,
    service: str = "",
    baseurl: str = "https://pass.sdu.edu.cn",
) -> dict:
    ss = Session()  # use session to keep cookies
    lt = ss.post(
        baseurl + "/cas/restlet/tickets",
        data=f"username={sduid}&password={password}",
    ).text
    st = ss.post(  # get service ticket
        baseurl + f"/cas/restlet/tickets/{lt}",
        data=f"service={service}",
    ).text
    if not st.startswith("ST-"):
        raise ValueError("Login failed, please check your credentials.")
    data = ss.get(
        baseurl + "/cas/p3/serviceValidate",
        params={"service": service, "ticket": st},
    ).text
    name = search(r"<cas:USER_NAME>(.*?)</cas:USER_NAME>", data).group(1)
    print(f"Hello {name}!")
    st = ss.post(  # get service ticket again, cause st is single-use
        baseurl + f"/cas/restlet/tickets/{lt}",
        data=f"service={service}",
    ).text
    ss.get(f"{service}&ticket={st}", allow_redirects=True)  # get cookies
    return {"cookies": {k: v for k, v in ss.cookies.items()}, "user": name}


if __name__ == "__main__":
    from getpass import getpass

    # example 1, aiassist
    sduid = input("SDU ID: ")
    password = getpass("Password: ")
    cookies = login(
        sduid,
        password,
        "https://aiassist.sdu.edu.cn/common/actionCasLogin?redirect_url=https%3A%2F%2Faiassist.sdu.edu.cn%2Fpage%2Fsite%2FnewPc%3Flogin_return%3Dtrue",
    )["cookies"]
    ss = Session()
    data = ss.get(
        "https://aiassist.sdu.edu.cn/site/user_info", cookies=cookies
    )  # get expiration time
    print(f"Hi {data.json()["d"]["user_name"]}, welcome to the SDU AI assistant!")
    print(
        {
            "cookies": {k: v for k, v in ss.cookies.items()},
            "expires": datetime.strptime(
                search(r"expires=([^;]+)", data.headers["Set-Cookie"]).group(1),
                "%a, %d-%b-%Y %H:%M:%S GMT",
            ).replace(tzinfo=timezone.utc),
        }
    )
    # example 2, service
    from uniform_login_des import strEnc

    ss = Session()
    cookies = login(
        sduid,
        password,
        service="https://service.sdu.edu.cn/tp_up/view?m=up",
    )["cookies"]
    info = ss.post(
        "https://service.sdu.edu.cn/tp_up/sys/uacm/profile/getUserById",
        json={"BE_OPT_ID": strEnc(sduid, "tp", "des", "param")},
        headers={
            "Content-Type": "application/json;charset=UTF-8",
        },
        cookies=cookies,
    ).json()
    print(info)
