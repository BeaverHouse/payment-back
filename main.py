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
    if (os.path.exists(excel_path)):
        os.remove(excel_path)
    with open("process.txt", "r+", encoding="utf8") as f:
        state = f.read().strip()
        if state == "_".join([name, year, month]):
            return {
                "message" : "already processing"
            }
        if (os.path.exists("screenshots/{}_{}_{}".format(name, year, month))):
            shutil.rmtree("screenshots/{}_{}_{}".format(name, year, month))
        for fi in files:
            crop_and_save(fi, "_".join([name, year, month]))
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
        return {
            "state": "complete"
        }
    else:
        img_exists = os.path.isdir("screenshots/{}_{}_{}".format(name, year, month))
        with open("process.txt", "r", encoding="utf8") as f:
            state = f.read()
        if img_exists and state=="_".join([name, year, month]):
            return {
                "state": "processing"
            }
        else:
            return {
                "state": "not found"
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

@app.get("/process/now")
def get_now():
    with open("process.txt", "r", encoding="utf8") as f:
        state = f.read().strip()
    return {
        "process" : state
    }
