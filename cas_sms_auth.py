from tkinter import Tk, Label, PhotoImage
from httpx import Client
from random import random

mobile = ""  # Your mobile number
service = ""  #  "https://aiassist.sdu.edu.cn/common/actionCasLogin?redirect_url=https%3A%2F%2Faiassist.sdu.edu.cn%2Fpage%2Fsite%2FnewPc%3Flogin_return%3Dtrue"
client = Client()

if mobile == "":
    mobile = input("手机号: ")
if service == "":
    exit("请填写service")
while True:
    window = Tk()
    window.title("图片验证码")
    window.bind("<Escape>", lambda e: window.destroy())
    photo = PhotoImage(data=client.get("https://pass.sdu.edu.cn/cas/code").content)
    img_label = Label(window, image=photo)
    img_label.pack(pady=10)
    window.mainloop()
    imgcode = input("图片验证码: ")
    url = (
        client.post(
            "https://pass.sdu.edu.cn/cas/loginByMorE",
            data={
                "method": "sendMobileCode",
                "sendConfirm": imgcode,
                "mobile": mobile,
                "random": random(),
            },
        )
        .json()
        .get("redirectUrl")
    )
    if url == "login":
        break
    else:
        print("图片验证码错误，请重试。")

mobilecode = input("短信验证码: ")
if (
    url := client.post(
        "https://pass.sdu.edu.cn/cas/loginByMorE",
        data={
            "method": "login",
            "mobile": mobile,
            "mobileCode": mobilecode,
            "random": random(),
            "service": service,
        },
    )
    .json()
    .get("redirectUrl")
):
    res = client.get(url, follow_redirects=True)
    print(client.cookies)
