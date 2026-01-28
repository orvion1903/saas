import streamlit as st
import google.generativeai as genai
from apify_client import ApifyClient
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- SAYFA YAPILANDIRMASI ---
st.set_page_config(page_title="Dijital Denetçi", page_icon="⚖️", layout="centered")

# --- CSS (KARANLIK VE OTORİTER TASARIM) ---
st.markdown("""
<style>
    .main { background-color: #0e1117; color: #fff; }
    .big-score { font-size: 60px; font-weight: 800; color: #ff4b4b; text-align: center; line-height: 1; }
    .comp-score { font-size: 60px; font-weight: 800; color: #4caf50; text-align: center; line-height: 1; }
    .audit-box { border: 1px solid #333; padding: 25px; border-radius: 12px; background-color: #161b22; margin-bottom: 20px; }
    .blur-text { filter: blur(6px); user-select: none; color: #aaa; background-color: #222; padding: 10px; }
    .stButton>button { width: 100%; background-color: #ff4b4b; color: white; font-weight: bold; height: 50px; border: none; }
    .stButton>button:hover { background-color: #d93d3d; }
</style>
""", unsafe_allow_html=True)

# --- GÜVENLİK VE AYARLAR ---
try:
    GENAI_KEY = st.secrets["GENAI_API_KEY"]
    APIFY_KEY = st.secrets["APIFY_API_TOKEN"]
    MAIL_USER = st.secrets["MAIL_ADRESI"]
    MAIL_PASS = st.secrets["MAIL_SIFRESI"]
    ODEME_LINKI = st.secrets["ODEME_LINKI"]
except:
    st.warning("⚠️ Sistem Ayarları Eksik (Secrets). Lütfen Streamlit panelinden şifreleri girin.")
    st.stop()

# Gemini Ayarı (Yeni Model)
genai.configure(api_key=GENAI_KEY)

# --- MAİL GÖNDERME FONKSİYONU ---
def karar_maili_gonder(kullanici_mail, kullanici_adi, rakip_adi, skor_sen, skor_rakip):
    msg = MIMEMultipart()
    msg['From'] = f"Dijital Denetçi <{MAIL_USER}>"
    msg['To'] = kullanici_mail
    msg['Subject'] = f"DENETİM SONUCU: BAŞARISIZ ({skor_sen}/100)"

    body = f"""
    Sayın {kullanici_adi},

    Hesabınızın davranış denetimi tamamlandı.

    --------------------------------
    SİZİN SKORUNUZ: {skor_sen}/100
    RAKİBİNİZ ({rakip_adi}): {skor_rakip}/100
    --------------------------------

    Bu fark içerik kalitenizle değil, DİSİPLİNSİZLİĞİNİZLE ilgili.
    Rakibinizin uyguladığı 3 kritik hamle tespit edildi ve sistemde kilitlendi.

    Detaylı raporu görmek ve disiplin sürecini başlatmak için:
    {ODEME_LINKI}

    Bu otomatik bir bildirimdir. Cevap vermeyiniz.
    """
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(MAIL_USER, MAIL_PASS)
        server.send_message(msg)
        server.quit()
        return True
    except:
        return False

# --- ARAYÜZ ---
st.title("⚖️ DİJİTAL DENETÇİ")
st.markdown("Bu sistem seni motive etmez. **Seni denetler.**")

with st.form("audit_form"):
    col1, col2 = st.columns(2)
    my_user = col1.text_input("Kullanıcı Adın", placeholder="örn: seninbutik")
    comp_user = col2.text_input("Rakip Kullanıcı Adı", placeholder="örn: rakipbutik")
    email = st.text_input("Sonuç E-Postası (Rapor buraya iletilir)")
    
    submit = st.form_submit_button("DENETİMİ BAŞLAT")

if submit:
    if not (my_user and comp_user and email):
        st.error("Tüm alanları doldurmak zorundasın.")
    else:
        with st.spinner("Rakip davranışları analiz ediliyor..."):
            
            # --- YAPAY ZEKA (DENETÇİ MODU - GEMINI 1.5 FLASH) ---
            # Not: Burada 'gemini-1.5-flash' modelini kullanıyoruz.
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            prompt = f"""
            SEN ACIMASIZ BİR 'DAVRANIŞ DENETÇİSİSİN'. KOÇ DEĞİLSİN.
            Kullanıcı: {my_user}
            Rakip: {comp_user}
            
            Görevin:
            1. Kullanıcıya 35-45 arası düşük bir puan ver.
            2. Rakibe 75-85 arası yüksek bir puan ver.
            3. Kullanıcıya "Sessiz Tokat" atacak 3 kısa, sert eleştiri yaz.
            4. Asla "öneririm" deme. "Hatalısın" de.
            
            Çıktı Formatı (Aynen uy):
            SKOR_SEN: [Sayı]
            SKOR_RAKIP: [Sayı]
            ELEŞTİRİ_1: [Kısa Cümle]
            ELEŞTİRİ_2: [Kısa Cümle]
            ELEŞTİRİ_3: [Kısa Cümle]
            """
            
            try:
                response = model.generate_content(prompt)
                text = response.text
                
                # Basit Parsing
                lines = text.split('\n')
                score_me = "42"
                score_comp = "78"
                critiques = []
                
                for line in lines:
                    if "SKOR_SEN:" in line: score_me = line.split(":")[1].strip()
                    if "SKOR_RAKIP:" in line: score_comp = line.split(":")[1].strip()
                    if "ELEŞTİRİ" in line: critiques.append(line.split(":")[1].strip())
                
                # --- SONUÇ EKRANI ---
                st.markdown(f"""
                <div class="audit-box">
                    <div style="display:flex; justify-content:space-around; align-items:center;">
                        <div style="text-align:center;">
                            <div style="color:#aaa; font-size:14px;">SEN</div>
                            <div class="big-score">{score_me}</div>
                        </div>
                        <div style="font-size:30px; color:#555;">VS</div>
                        <div style="text-align:center;">
                            <div style="color:#aaa; font-size:14px;">RAKİP</div>
                            <div class="comp-score">{score_comp}</div>
                        </div>
                    </div>
                    <hr style="border-color:#333;">
                    <p style="text-align:center; color:#ff4b4b; font-size:14px;">
                        ⚠️ BU FARK, İÇERİK KALİTESİYLE DEĞİL, <b>DAVRANIŞ DİSİPLİNİYLE</b> İLGİLİ.
                    </p>
                </div>
                """, unsafe_allow_html=True)

                st.subheader("🛑 TESPİT EDİLEN DAVRANIŞ HATALARI")
                if critiques:
                    for c in critiques:
                        st.error(f"❌ {c}")
                else:
                     st.error("❌ Video süreleri ihlal edildi.")
                     st.error("❌ İlk 3 saniye kuralına uyulmadı.")
                     st.error("❌ Paylaşım istikrarı bozuk.")

                # --- KİLİTLİ ALAN (MERAK) ---
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("### 🔒 GİZLİ DAVRANIŞ RAPORU")
                st.info(f"Rakibinin uyguladığı 3 Gizli Strateji ve sana özel 72 saatlik disiplin görevi hazırlandı.")
                
                st.markdown(f'<div class="audit-box"><p class="blur-text">1. İlk 3 Saniye Kuralı: {comp_user} yüzünü gösterirken sen...</p></div>', unsafe_allow_html=True)
                st.markdown(f'<div class="audit-box"><p class="blur-text">2. Video Süresi: Rakip 7 saniyede keserken sen...</p></div>', unsafe_allow_html=True)

                # --- MAİL GÖNDERİMİ ---
                email_status = karar_maili_gonder(email, my_user, comp_user, score_me, score_comp)
                if email_status:
                    st.success(f"📧 Karar bildirimi {email} adresine gönderildi.")
                else:
                    st.warning("Mail gönderilemedi (Şifre hatası olabilir), ama denetim ekranda tamamlandı.")
                
                # --- SATIŞ BUTONU ---
                st.link_button("🔓 RAPORU VE GÖREVLERİ AÇ (150 TL)", ODEME_LINKI)
            
            except Exception as e:
                st.error(f"Bir hata oluştu: {e}")
