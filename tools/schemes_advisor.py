import io
import re
import socket
import streamlit as st
from groq import Groq
from gtts import gTTS

# Force IPv4 globally so Groq & gTTS respond in <1s on Windows/Pakistani ISPs
_orig_getaddrinfo = socket.getaddrinfo
socket.getaddrinfo = lambda host, port, family=0, type=0, proto=0, flags=0: _orig_getaddrinfo(
    host, port, socket.AF_INET, type, proto, flags
)
socket.setdefaulttimeout(12.0)

VERIFIED_PK_SCHEMES = [
    {
        "id": "kissan_card",
        "title": "Chief Minister Punjab Kissan Card",
        "province": "Punjab",
        "benefit": "Bila sood (0% markup) zarai qarza PKR 150,000 har fasal ke liye (PKR 30,000 fi acre, zyada se zyada 5 acre tak) jo sirf beej, khad (Urea/DAP) aur spray kharidne ke liye istemal hota hai.",
        "eligibility": "Punjab ke woh kisaan jin ke paas 1 se 12.5 acre zarai zameen ho, Punjab Land Records Authority (PLRA) mein record darj ho, apna CNIC aur apne CNIC par registered mobile SIM ho, aur kisi bank ke defaulter na hon.",
        "how_to_apply": "Apne mobile se 'PKC <space> Apna CNIC Number' likh kar 8070 par SMS bhejein, ya qareebi Agriculture Extension Office / Bank of Punjab (BOP) branch ja kar biometric tasdeeq karwayein.",
        "official_url": "https://agripunjab.gov.pk",
        "helpline": "0800-17000 (Punjab Agriculture Helpline)",
    },
    {
        "id": "green_tractor",
        "title": "CM Green Tractor Scheme",
        "province": "Punjab",
        "benefit": "Pakistan mein banne wale 50 HP se 85 HP tractor par hukoomat ki taraf se PKR 10 Lakh (1,000,000) ki seedhi subsidy, jo computerized qurandazi (balloting) ke zariye di jati hai.",
        "eligibility": "Punjab ka mustaqil rehaishi kisaan jis ke paas 1 acre se 50 acre tak zarai zameen ho aur valid CNIC mojood ho.",
        "how_to_apply": "Official portal https://gts.punjab.gov.pk par online form jama karwayein ya apne zila ke Deputy Director Agriculture (Extension) office mein darkhwast jama karein.",
        "official_url": "https://gts.punjab.gov.pk",
        "helpline": "0800-17000",
    },
    {
        "id": "solar_tubewell",
        "title": "Agricultural Tube Well Solarization Scheme",
        "province": "Punjab / Federal",
        "benefit": "Diesel ya bijli wale zarai tube well ko solar par muntaqil karne ke liye 50% se 60% sarkari subsidy (PKR 5 Lakh se 10 Lakh tak, 10kW, 15kW aur 20kW system ke mutabiq).",
        "eligibility": "Kam az kam 1 acre zarai zameen ka malik kisaan jis ke paas pehle se registered electric ya diesel tube well aur valid CNIC ho.",
        "how_to_apply": "Official website https://agripunjab.gov.pk par solarization portal ke zariye online apply karein ya apne zila ke Water Management / Agriculture Engineering office se rabta karein.",
        "official_url": "https://agripunjab.gov.pk",
        "helpline": "0800-17000",
    },
    {
        "id": "pm_agri_loan",
        "title": "Prime Minister Youth Business & Agriculture Loan Scheme (PMYB&ALS)",
        "province": "Poora Pakistan (KPK, Punjab, Sindh, Balochistan)",
        "benefit": "Tier-1: PKR 5 Lakh tak bilkul bila sood (0% markup). Tier-2: PKR 5 Lakh se 15 Lakh tak sirf 5% markup par. Tier-3: PKR 15 Lakh se 75 Lakh tak 7% markup par faslon, dairy, livestock, drip irrigation aur zarai machinery ke liye.",
        "eligibility": "21 se 45 saal ke Pakistani shehri jin ke paas valid CNIC aur kheti-bari ya agri-business ka mansooba ho.",
        "how_to_apply": "Official portal https://pmyp.gov.pk par online apply karein aur ZTBL, Bank of Khyber, NBP, HBL ya UBL select karein.",
        "official_url": "https://pmyp.gov.pk",
        "helpline": "051-111-627-627",
    },
    {
        "id": "ztbl_zarai_loans",
        "title": "ZTBL Zarai Taraqiati Bank Qarza Schemes",
        "province": "Poora Pakistan (KPK, Karak, Punjab, Sindh, Balochistan)",
        "benefit": "Sada Bahar Scheme aur Asaan Zarai Karza ke tehat beej, khad aur spray ke liye fasli qarza, aur tractor, laser land leveler aur baghaat ke liye taraqiati qarza.",
        "eligibility": "Zameen ke malik ya registered muzare (tenants) jin ke paas Revenue Department ki jari karda Zarai Passbook aur valid CNIC ho.",
        "how_to_apply": "Apne qareebi ZTBL branch (maslan ZTBL Karak branch) mein CNIC, Zarai Passbook aur 2 tasveerein le kar jayein, ya maloomat ke liye https://www.ztbl.com.pk dekhein.",
        "official_url": "https://www.ztbl.com.pk",
        "helpline": "051-9252798",
    },
    {
        "id": "kpk_agri_subsidy",
        "title": "Khyber Pakhtunkhwa (KPK) Agriculture Subsidies & Kissan Package",
        "province": "Khyber Pakhtunkhwa (KPK)",
        "benefit": "Sarkari subsidy par tasdeeq-shuda gandum aur makai ke beej, phalon ke poday (zaitoon, malta), drip/sprinkler aabpashi nizam par 60% se 80% subsidy, aur muft soil testing.",
        "eligibility": "KPK ke kisaan jin ke paas valid CNIC aur zameen ki malkiyat ya theke (tenancy) ka saboot ho.",
        "how_to_apply": "Apne zila (maslan Karak, Kohat, Peshawar, Mardan) ke District Director Agriculture Extension office mein CNIC aur Fard ke sath registration karwayein, ya https://agriculture.kp.gov.pk visit karein.",
        "official_url": "https://agriculture.kp.gov.pk",
        "helpline": "091-9210119 (Agriculture Department KPK)",
    },
]


@st.cache_resource
def _get_cached_groq_client(api_key: str) -> Groq:
    return Groq(api_key=api_key.strip(), timeout=12.0, max_retries=0)


def _build_schemes_context() -> str:
    blocks = []
    for s in VERIFIED_PK_SCHEMES:
        blocks.append(
            f"Scheme: {s['title']} ({s['province']})\n"
            f"- Faida / Raqam: {s['benefit']}\n"
            f"- Ahliyat (Eligibility): {s['eligibility']}\n"
            f"- Apply Tariqa: {s['how_to_apply']}\n"
            f"- Official Website Link: {s['official_url']}\n"
            f"- Helpline: {s['helpline']}"
        )
    return "\n\n".join(blocks)


SCHEMES_ROMAN_SYSTEM_PROMPT = f"""
Aap "Kisaan Dost" ke Government Agricultural Schemes Advisor hain.
Neeche Pakistani hukoomat ki verified zarai schemes ka mukammal database diya gaya hai:

{_build_schemes_context()}

SAKHT HIDAYAT (In par 100% amal karein):
1. Sirf upar diye gaye verified database ki buniyad par mukammal, durust aur asaan jawab dein. Apni taraf se koi jhooti raqam ya link na banayein.
2. Jawab hamesha saaf aur asaan ROMAN URDU (English alphabet mein likhi Urdu, jaise "Aap ko is scheme mein 5 lakh tak qarza mil sakta hai") mein likhein. Urdu Nastaliq script har-giz istemal na karein.
3. Jawab mein ** stars ya # symbols istemal na karein. Har hisse ki heading bilkul is tarah alag line par likhein:
   Scheme Ka Naam:
   Faida Aur Raqam:
   Ahliyat (Eligibility):
   Apply Karne Ka Tariqa:
   Official Portal Link: (yahan poora https://... URL zaroor likhein)
   Helpline Number:
""".strip()


def transcribe_scheme_voice(audio_bytes: bytes, api_key: str) -> dict:
    if not audio_bytes or len(audio_bytes) < 500:
        return {"success": False, "error": "Awaz bohat mukhtasar hai. Meharbani karke mic daba kar 2 second wazeh bolein."}
    if not api_key or "YAHAN_APNI" in api_key:
        return {"success": False, "error": "Groq API Key mojood nahi hai. secrets.toml check karein."}

    filename = "scheme_q.wav"
    if audio_bytes[:4] == b"OggS":
        filename = "scheme_q.ogg"
    elif audio_bytes[:4] == b"\x1a\x45\xdf\xa3":
        filename = "scheme_q.webm"

    try:
        client = _get_cached_groq_client(api_key)
        res = client.audio.transcriptions.create(
            file=(filename, audio_bytes),
            model="whisper-large-v3-turbo",
            language="ur",
            prompt="Kissan Card, Green Tractor Scheme, Solar Tube Well subsidy, ZTBL loan, KPK Kissan package.",
            temperature=0.0,
        )
        text = (res.text or "").strip()
        if not text:
            return {"success": False, "error": "Awaz saaf sunai nahi di, dobara bolein."}
        return {"success": True, "text": text}
    except Exception as e:
        return {"success": False, "error": f"Awaz samajhne mein masla aaya: {str(e)}"}


def _linkify_and_format_html(raw_text: str) -> str:
    """Converts raw text + https:// URLs into clean LTR HTML with clickable external links."""
    lines_html = []
    headings = (
        "Scheme Ka Naam:",
        "Faida Aur Raqam:",
        "Ahliyat (Eligibility):",
        "Apply Karne Ka Tariqa:",
        "Official Portal Link:",
        "Helpline Number:",
    )
    for raw_ln in raw_text.splitlines():
        ln = re.sub(r"[*#`]", "", raw_ln).strip()
        if not ln:
            continue
        ln = re.sub(
            r"(https?://[^\s<>)\]]+)",
            r'<a href="\1" target="_blank" rel="noopener noreferrer" '
            r'style="color: #38bdf8; font-weight: 700; text-decoration: underline; background: rgba(56,189,248,0.18); padding: 3px 10px; border-radius: 6px; display: inline-block; margin-top: 2px;">'
            r'&#128279; \1 (Click Here to Open)</a>',
            ln,
        )
        is_heading = any(ln.startswith(h) for h in headings)
        if is_heading:
            parts = ln.split(":", 1)
            title_part = parts[0] + ":"
            rest_part = parts[1].strip() if len(parts) > 1 else ""
            lines_html.append(
                f'<div style="margin-top: 10px; line-height: 1.7;">'
                f'<span style="color: #fde047; font-weight: 800;">{title_part}</span> '
                f'<span style="color: #ffffff;">{rest_part}</span></div>'
            )
        else:
            lines_html.append(f'<div style="margin-top: 4px; color: #ecfdf5; line-height: 1.7;">{ln}</div>')
    return "".join(lines_html)


def _generate_voice_note(roman_text: str) -> bytes | None:
    try:
        clean_txt = re.sub(r"[*#`]", "", roman_text)
        clean_txt = re.sub(r"https?://[^\s]+", "official website link screen par diya gaya hai", clean_txt)
        clean_txt = re.sub(r"\s+", " ", clean_txt).strip()
        if not clean_txt:
            return None
        buf = io.BytesIO()
        tts = gTTS(text=clean_txt, lang="ur", slow=False)
        tts.write_to_fp(buf)
        buf.seek(0)
        return buf.read()
    except Exception:
        return None


def ask_schemes_with_voice_and_text(
    user_query: str,
    api_key: str,
    chat_history: list[dict] | None = None,
) -> dict:
    if not user_query or not user_query.strip():
        return {"success": False, "error": "Meharbani karke scheme ke baray mein sawal likhein ya mic se bolein."}
    if not api_key or "YAHAN_APNI" in api_key:
        return {"success": False, "error": "Groq API Key mojood nahi hai. secrets.toml check karein."}

    try:
        client = _get_cached_groq_client(api_key)
        messages = [{"role": "system", "content": SCHEMES_ROMAN_SYSTEM_PROMPT}]

        if chat_history:
            for turn in chat_history[-3:]:
                if turn.get("user") and turn.get("assistant_raw"):
                    messages.append({"role": "user", "content": turn["user"]})
                    messages.append({"role": "assistant", "content": turn["assistant_raw"]})

        messages.append({"role": "user", "content": user_query.strip()})

        completion = None
        last_err = None
        for model_name in ("llama-3.3-70b-versatile", "openai/gpt-oss-20b"):
            try:
                completion = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    temperature=0.1,
                    max_tokens=850,
                )
                break
            except Exception as err:
                last_err = err
                if "401" in str(err):
                    raise err

        if completion is None and last_err is not None:
            raise last_err

        raw_reply = (completion.choices[0].message.content or "").strip()
        if not raw_reply:
            return {"success": False, "error": "Jawab masool nahi hua, dobara koshish karein."}

        formatted_html = _linkify_and_format_html(raw_reply)
        audio_bytes = _generate_voice_note(raw_reply)

        return {
            "success": True,
            "reply": formatted_html,
            "raw_reply": raw_reply,
            "audio_bytes": audio_bytes,
        }

    except Exception as e:
        return {"success": False, "error": f"Schemes Advisor Error: {str(e)}"}
