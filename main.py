from fastapi import FastAPI, Form, UploadFile, BackgroundTasks, HTTPException
from fastapi.responses import RedirectResponse, FileResponse
from img_process import crop_and_save
from selenium_clova import file_ocr
import os
from pathlib import Path
import shutil

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    Path("screenshots").mkdir(parents=True, exist_ok=True)
    with open("process.txt", "w", encoding="utf8") as f:
        f.write("Idle")


@app.get("/", include_in_schema=False)
def read_root():
    return RedirectResponse("/docs")


@app.post("/process")
def crop_and_process(
    files: list[UploadFile], 
    background_tasks: BackgroundTasks,
    name: str = Form(), 
    year: str = Form(),
    month: str = Form(),
):  
    excel_path = 'result/{} {}년 {}월 법인카드 내역.xlsx'.format(name, year, month)
    # 이미 엑셀 파일이 있으면 삭제하고 시작
    if (os.path.exists(excel_path)):
        os.remove(excel_path)
    with open("process.txt", "r+", encoding="utf8") as f:
        state = f.read().strip()
        if state == "_".join([name, year, month]):
            return {
                "message" : "already processing"
            }
        # 스크린샷이 있으면 삭제하고 새로 등록 (현재 실행중이 아닐 경우 갱신됨)
        if (os.path.exists("screenshots/{}_{}_{}".format(name, year, month))):
            shutil.rmtree("screenshots/{}_{}_{}".format(name, year, month))
        for fi in files:
            crop_and_save(fi, "_".join([name, year, month]))
        # 앱이 대기중이면 state 바꾸고 프로세스 실행
        # (이미 실행중이면 그거 끝나고 file_ocr 함수에서 순차적으로 실행될 것)
        if state == "Idle":
            f.seek(0)
            f.truncate()
            f.write("_".join([name, year, month]))
            background_tasks.add_task(file_ocr, name, int(year), int(month))
    return {
        "message" : "success"
    }

@app.get("/process/status")
def get_file(
    name: str = "", 
    year: str = "",
    month: str = ""
):
    file_name = '{} {}년 {}월 법인카드 내역.xlsx'.format(name, year, month)
    file_path = "result/" + file_name
    if os.path.exists(file_path):
        # 1. 엑셀 파일이 존재하는 경우 완료된 것
        return {
            "state": "complete",
            "order": -1
        }
    else:
        # 2. 엑셀파일이 없는 경우
        img_exists = os.path.isdir("screenshots/{}_{}_{}".format(name, year, month))
        with open("process.txt", "r", encoding="utf8") as f:
            state = f.read()
        if img_exists:
            my_id = "_".join([name, year, month])
            if state==my_id:
                # 2-1. 이미지는 있고 state가 자기 차례인 경우
                return {
                    "state": "processing",
                    "order": 0
                }
            else:             
                # 2-2. 이미지는 있는데 state가 자기 차례가 아닌 경우  
                paths = list(map(
                    lambda x: x.name ,sorted(Path("screenshots").iterdir(), key=os.path.getmtime)
                ))
                return {
                    "state": "waiting",
                    "order": paths.index(my_id) + 1
                }
        else:
            # 2-3. 이미지도 엑셀도 없는 경우 그냥 아무것도 아님
            return {
                "state": "not found",
                "order": -1
            }
        
@app.get("/download")
def get_file(
    name: str = "", 
    year: str = "",
    month: str = ""
):
    file_name = '{} {}년 {}월 법인카드 내역.xlsx'.format(name, year, month)
    file_path = "result/" + file_name
    if os.path.exists(file_path):
        return FileResponse(
            path= "result/" + file_name, 
            filename= file_name,
            media_type= "application/`vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        raise HTTPException(400)