from fastapi import FastAPI, Form, UploadFile, BackgroundTasks
from fastapi.responses import RedirectResponse, FileResponse
from img_process import crop_and_save
from selenium_clova import file_ocr
import os

app = FastAPI()


@app.get("/", include_in_schema=False)
def read_root():
    return RedirectResponse("/docs")


@app.post("/process")
async def crop_and_process(
    files: list[UploadFile], 
    background_tasks: BackgroundTasks,
    name: str = Form(), 
    year: str = Form(),
    month: str = Form(),
):
    os.remove('result/{} {}년 {}월 법인카드 내역.xlsx'.format(name, year, month))
    for f in files:
        await crop_and_save(f, "_".join([name, year, month]))
    background_tasks.add_task(file_ocr, name, int(year), int(month))
    return {
        "message" : "success"
    }

@app.get("/process/state")
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
        img_exists = os.path.isdir("_".join([name, year, month]))
        if img_exists:
            return {
                "state": "processing"
            }
        else:
            return {
                "state": "not found"
            }
