import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from pypdf import PdfReader
from google import genai
from dotenv import load_dotenv

# 1. 금고(.env)에서 구글 비밀번호 꺼내서 최신 Gemini 준비
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None

app = FastAPI()

@app.get("/")
def read_root():
    return FileResponse("index.html")

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    if not client:
        raise HTTPException(status_code=500, detail=".env 파일에서 GEMINI_API_KEY를 찾지 못했습니다.")

    try:
        print(f"[1/3] '{file.filename}' PDF 글자 추출 시작...")
        reader = PdfReader(file.file)
        text = ""
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
            if len(text) >= 3000:
                break

        if not text.strip():
            raise HTTPException(status_code=400, detail="PDF에서 글자를 추출하지 못했습니다. (글자 드래그가 안 되는 이미지형 PDF일 수 있습니다.)")

        short_text = text[:3000]
        prompt = f"너는 연구 논문 요약 전문가야. 다음 텍스트의 핵심 내용을 한국어로 3줄 요약해줘:\n\n{short_text}"

        # 혼잡도가 낮은 무료 모델 순서대로 시도 (자동 백업)
        free_models = ["gemini-3.5-flash-lite", "gemini-3.6-flash", "gemini-3.8-flash"]
        last_error = None

        for model_name in free_models:
            try:
                print(f"[2/3] '{model_name}' 모델로 요약 요청 중...")
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                )
                print(f"[3/3] AI 요약 완료! (사용 모델: {model_name})")
                return {
                    "filename": file.filename,
                    "used_model": model_name,
                    "summary": response.text
                }
            except Exception as e:
                print(f" -> {model_name} 일시 혼잡, 다음 모델로 전환합니다...")
                last_error = e
                continue

        raise last_error

    except HTTPException:
        raise
    except Exception as e:
        print(f"[오류 발생] {str(e)}")
        raise HTTPException(status_code=500, detail=f"처리 중 오류 발생: {str(e)}")