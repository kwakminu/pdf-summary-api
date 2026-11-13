from fastapi import FastAPI, UploadFile, File

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "AI 논문 요약 서버가 정상 작동 중입니다."}

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    return{
        "filename": file.filename,
        "content_type": file.content_type,
        "status" : "서버에 파일 도착 완료!"
    }