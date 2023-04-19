import clipboard
import re
from dotenv import load_dotenv
import os

load_dotenv()

def parse_text(rawdata):
    card = os.getenv("card", "카드")

    # li = rawdata.replace(">", "").split("\r\n")
    li = rawdata.replace(">", "").split("\n")

    arr = []
    dic = {}
    for l in li:
        s = l.strip()
        if len(s) > 1 and s[-1] == "원":
            # 새로운 term이 시작되면 arr에 추가하고 초기화
            if "month" in dic:
                arr.append(dic)
            dic = {}
            
            # 원이 따로 인식되면 숫자에 붙임
            while not s[-2].isdigit():
                s = s.replace(" 원", "원")

            sp = s.split(" ")
            dic["shop_name"] = " ".join(sp[0:-1])
            dic["price"] = int(re.sub("\D", "", sp[-1].replace(",", "")))
        elif "승인취소" in s:
            dic = {}
        elif card in s:
            if "shop_name" in dic:
                sp = s.split(" ")
                dic["month"] = int(re.sub("\D", "", sp[0]))
                dic["day"] = int(re.sub("\D", "", sp[1]))
    
    if "month" in dic:
        arr.append(dic)

    return arr

if __name__ == "__main__":
    result = clipboard.paste()
    print(parse_text(result))