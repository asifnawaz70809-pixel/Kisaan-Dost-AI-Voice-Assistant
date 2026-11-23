import os
import re
import io
import time
import wave
import socket
import tempfile
import urllib3.util.connection as urllib3_cn
import numpy as np
from groq import Groq
from gtts import gTTS

# Force IPv4 globally so Groq & gTTS respond in <1s on Windows/Pakistani ISPs
_orig_getaddrinfo = socket.getaddrinfo


def _ipv4_only_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    return _orig_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)


socket.getaddrinfo = _ipv4_only_getaddrinfo
socket.setdefaulttimeout(12.0)
urllib3_cn.allowed_gai_family = lambda: socket.AF_INET

URDU_AGRI_INITIAL_PROMPT = (
    "ہیلو السلام علیکم کسان دوست، مجھے بتائیں کہ میں اپنی گندم پر کب سپرے کروں اور کتنا ٹائم سپرے کروں۔ "
    "فی ایکڑ، کتنی بار، کتنے دن بعد، صبح سویرے، شام کے وقت، چاول، کپاس، مکئی، آلو، ٹماٹر، آم، "
    "کھاد، یوریا، ڈی اے پی، پیلا زنگ، سنڈی، آبپاشی، منڈی ریٹ، موسم، بارش، فصل کی بیماری اور علاج۔"
)

KISAAN_URDU_SYSTEM_PROMPT = "\n".join([
    "آپ کسان دوست ہیں جو پاکستان کے کسانوں کے لیے ایک انتہائی تجربہ کار اور مستند زرعی ماہر ہیں",
    "سخت ترین ہدایات جن پر ہر حال میں عمل کرنا ضروری ہے:",
    "1. کسان کا سوال آواز سے لکھا گیا ہے اس لیے اس میں املا یا تلفظ کی معمولی غلطیاں ہو سکتی ہیں جیسے ٹیم کا مطلب ٹائم یا وقت، سپری کا مطلب سپرے، مجھو کا مطلب مجھے، اور حلو کا مطلب ہیلو ہے۔ آپ ہمیشہ سیاق و سباق سے کسان کا اصل مقصد سمجھ کر درست جواب دیں",
    "2. صرف اور صرف خالص، آسان اور مستند اردو رسم الخط میں جواب دیں۔ جواب میں انگریزی یا رومن اردو کا ایک بھی لفظ نہ لکھیں",
    "3. تمام زرعی پیمائشیں پاکستان کے معیار کے مطابق فی ایکڑ اور ٹینکی کے حساب سے بتائیں نہ کہ ہیکٹر میں۔ مثال کے طور پر عام فصلوں میں فی ایکڑ سو سے ایک سو بیس لیٹر پانی میں دوائی ملا کر سپرے کیا جاتا ہے",
    "4. جب کسان پوچھے کہ کب اور کتنا ٹائم یا کتنی بار سپرے کروں تو واضح طور پر تین باتیں بتائیں: پہلا کہ دن کے کس وقت سپرے کرنا ہے یعنی صبح سویرے یا شام کے وقت، دوسرا کہ ایک ایکڑ میں عام طور پر پندرہ سے بیس منٹ میں تسلی بخش سپرے مکمل ہو جاتا ہے تاکہ پتے اچھی طرح تر ہو جائیں، اور تیسرا کہ بیماری کی شدت کے مطابق سات سے دس دن کے وقفے سے دوبارہ سپرے کیا جاتا ہے",
    "5. جواب مختصر، واضح اور چار سے پانچ سادہ جملوں میں رکھیں اور مارک ڈاؤن علامات جیسے ستارے یا ہیش یا گنتی کے نشان ہرگز استعمال نہ کریں تاکہ آواز میں سننے میں بالکل صاف لگے",
])

_whisper_cache = {}


def _detect_audio_filename(audio_bytes: bytes) -> str:
    if audio_bytes[:4] == b"RIFF":
        return "farmer_audio.wav"
    if audio_bytes[:4] == b"OggS":
        return "farmer_audio.ogg"
    if audio_bytes[:4] == b"\x1a\x45\xdf\xa3":
        return "farmer_audio.webm"
    return "farmer_audio.wav"


def _wav_bytes_to_16k_float32(audio_bytes: bytes) -> np.ndarray:
    with wave.open(io.BytesIO(audio_bytes), "rb") as wf:
        n_channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        framerate = wf.getframerate()
        n_frames = wf.getnframes()
        raw_frames = wf.readframes(n_frames)

    if sampwidth == 2:
        audio = np.frombuffer(raw_frames, dtype=np.int16).astype(np.float32) / 32768.0
    elif sampwidth == 4:
        audio = np.frombuffer(raw_frames, dtype=np.int32).astype(np.float32) / 2147483648.0
    elif sampwidth == 1:
        audio = (np.frombuffer(raw_frames, dtype=np.uint8).astype(np.float32) - 128.0) / 128.0
    else:
        raise ValueError(f"Unsupported WAV sample width: {sampwidth}")

    if n_channels > 1:
        audio = audio.reshape(-1, n_channels).mean(axis=1)

    if framerate != 16000 and len(audio) > 0:
        target_len = int(round(len(audio) * 16000 / framerate))
        old_idx = np.linspace(0, len(audio) - 1, num=len(audio))
        new_idx = np.linspace(0, len(audio) - 1, num=target_len)
        audio = np.interp(new_idx, old_idx, audio).astype(np.float32)

    return audio


def _transcribe_via_groq_whisper(audio_bytes: bytes, api_key: str) -> dict:
    if not api_key or "YAHAN_APNI" in api_key:
        return {"success": False, "error": "Groq API Key موجود نہیں ہے۔ secrets.toml چیک کریں"}

    t0 = time.time()
    filename = _detect_audio_filename(audio_bytes)
    client = Groq(api_key=api_key.strip(), timeout=12.0, max_retries=0)
    last_err = None

    for stt_model in ("whisper-large-v3-turbo", "whisper-large-v3"):
        try:
            transcription = client.audio.transcriptions.create(
                file=(filename, audio_bytes),
                model=stt_model,
                language="ur",
                prompt=URDU_AGRI_INITIAL_PROMPT,
                temperature=0.0,
            )
            text = (transcription.text or "").strip()
            print(f"[Voice 1/3] STT Done in {time.time() - t0:.2f}s -> {text}", flush=True)
            if text:
                return {"success": True, "text": text}
        except Exception as e:
            last_err = e
            if "401" in str(e) or "invalid_api_key" in str(e).lower():
                return {"success": False, "error": "Groq API Key غلط ہے"}

    return {"success": False, "error": f"آواز پہچاننے میں مسئلہ آیا ({last_err})"}


def transcribe_urdu_audio(
    audio_bytes: bytes,
    model_size: str = "groq_turbo",
    groq_api_key: str = "",
) -> dict:
    if not audio_bytes or len(audio_bytes) < 500:
        return {"success": False, "error": "آواز بہت مختصر یا خالی ہے۔ کم از کم 2 سیکنڈ واضح بولیں"}

    if model_size != "base":
        return _transcribe_via_groq_whisper(audio_bytes, groq_api_key)

    temp_path = None
    try:
        import whisper

        if "base" not in _whisper_cache:
            _whisper_cache["base"] = whisper.load_model("base")

        try:
            audio_input = _wav_bytes_to_16k_float32(audio_bytes)
        except wave.Error:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                tmp_file.write(audio_bytes)
                temp_path = tmp_file.name
            audio_input = temp_path

        result = _whisper_cache["base"].transcribe(
            audio_input,
            language="ur",
            task="transcribe",
            fp16=False,
            initial_prompt=URDU_AGRI_INITIAL_PROMPT,
            condition_on_previous_text=False,
            temperature=0.0,
        )
        transcript = result.get("text", "").strip()
        if not transcript:
            return {"success": False, "error": "آپ کی آواز واضح سنائی نہیں دی، دوبارہ بولیں"}
        return {"success": True, "text": transcript}
    except Exception as e:
        return {"success": False, "error": f"لوکل وائس ماڈل میں مسئلہ آیا: {str(e)}"}
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass


def _clean_urdu_for_display_and_tts(raw_text: str) -> str:
    cleaned = re.sub(r"[*_#`~>|]", "", raw_text)
    cleaned = re.sub(r"^\s*[-•\d+\.]+\s*", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def get_urdu_ai_response(
    user_urdu_text: str,
    api_key: str,
    chat_history: list[dict] | None = None,
) -> dict:
    if not api_key or "YAHAN_APNI" in api_key:
        return {"success": False, "error": "Groq API Key موجود نہیں ہے۔ secrets.toml چیک کریں"}

    t0 = time.time()
    try:
        client = Groq(api_key=api_key.strip(), timeout=12.0, max_retries=0)
        messages = [{"role": "system", "content": KISAAN_URDU_SYSTEM_PROMPT}]

        if chat_history:
            for turn in chat_history[-4:]:
                if turn.get("user") and turn.get("assistant"):
                    messages.append({"role": "user", "content": turn["user"]})
                    messages.append({"role": "assistant", "content": turn["assistant"]})

        messages.append(
            {
                "role": "user",
                "content": f"کسان کا سوال: {user_urdu_text} (جواب صرف خالص اردو رسم الخط میں دیں)",
            }
        )

        completion = None
        last_err = None
        for model_name in ("openai/gpt-oss-20b", "llama-3.3-70b-versatile"):
            try:
                completion = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    temperature=0.3,
                    max_tokens=400,
                    top_p=0.9,
                )
                print(f"[Voice 2/3] LLM ({model_name}) Done in {time.time() - t0:.2f}s", flush=True)
                break
            except Exception as model_err:
                last_err = model_err
                if "401" in str(model_err) or "invalid_api_key" in str(model_err).lower():
                    raise model_err

        if completion is None and last_err is not None:
            raise last_err

        raw_reply = completion.choices[0].message.content or ""
        clean_reply = _clean_urdu_for_display_and_tts(raw_reply)
        if not clean_reply:
            return {"success": False, "error": "اے آئی سے جواب موصول نہیں ہوا"}

        return {"success": True, "reply": clean_reply}
    except Exception as e:
        return {"success": False, "error": f"Groq API میں خرابی: {str(e)}"}


def synthesize_urdu_speech(urdu_text: str) -> dict:
    t0 = time.time()
    try:
        tts_ready_text = _clean_urdu_for_display_and_tts(urdu_text)
        if not tts_ready_text:
            return {"success": False, "error": "آواز بنانے کے لیے اردو متن خالی ہے"}

        mp3_buffer = io.BytesIO()
        tts = gTTS(text=tts_ready_text, lang="ur", slow=False)
        tts.write_to_fp(mp3_buffer)
        mp3_buffer.seek(0)
        audio_out = mp3_buffer.read()
        print(f"[Voice 3/3] TTS Done in {time.time() - t0:.2f}s ({len(audio_out)} bytes)", flush=True)
        return {"success": True, "audio_bytes": audio_out}
    except Exception as e:
        return {"success": False, "error": f"اردو آواز تیار کرنے میں مسئلہ آیا: {str(e)}"}


def process_voice_pipeline(
    audio_bytes: bytes,
    groq_api_key: str,
    whisper_size: str = "groq_turbo",
    chat_history: list[dict] | None = None,
) -> dict:
    stt_res = transcribe_urdu_audio(audio_bytes, model_size=whisper_size, groq_api_key=groq_api_key)
    if not stt_res["success"]:
        return {"success": False, "stage": "STT", "error": stt_res["error"]}

    user_urdu = stt_res["text"]
    llm_res = get_urdu_ai_response(user_urdu, groq_api_key, chat_history=chat_history)
    if not llm_res["success"]:
        return {"success": False, "stage": "LLM", "transcript": user_urdu, "error": llm_res["error"]}

    ai_urdu = llm_res["reply"]
    tts_res = synthesize_urdu_speech(ai_urdu)
    if not tts_res["success"]:
        return {
            "success": True,
            "transcript": user_urdu,
            "reply": ai_urdu,
            "audio_bytes": None,
            "tts_warning": tts_res["error"],
        }

    return {
        "success": True,
        "transcript": user_urdu,
        "reply": ai_urdu,
        "audio_bytes": tts_res["audio_bytes"],
        "tts_warning": None,
    }
