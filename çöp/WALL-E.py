# MERHABA BEN'İM ADIM WALL-E BEN BİR ÇÖP TOPLAMA ROBOTUYUM
import cv2 # CV2 KAMERADAN İŞLEM YAPMAK İÇİN 
import mediapipe as mp # CV2NIN YARDIMCISI DIR EL TANIMAK İÇİN
import random # RANDOM RASGELE SAYI OLUŞTURMAK İÇİN 
import numpy as np # CV2'NIN YARDIMCISI DIR
from playsound import playsound # PLAYSOUND KONUSMALARI ÇALMAK İÇİN
from gtts import gTTS # GTTS KONUŞMA'SI İÇİN DİR
import os # OS KONUŞMALARI SILMEK İÇİN
import threading # aynı anda birden fazla işi YAPMAK İÇİN
import time # TİME ZAMAN EKLEMEK İÇİN
from PIL import ImageFont, ImageDraw, Image # GÖSREL , RESİM EKLEMEK İÇİN DİR

# --- AYARLAR VE DEĞİŞKENLER ---
konusuyor = False # KONUŞMUYORSA DEGYERİ FALSE DIR  
ayrisma_basladi = False # ---- AYRİŞTİRMA BUTTONUNA BASINMADIĞI SÜRECE FALSE DIR
dolum_zamanlari = {}
tutulan_cop_id = None
ana_yol = r"C:\Users\alico\Desktop\kodlar\çöp\\" # ÇÖP RESİMLERİN ANA YOLUDUR
font_path = "C:/Windows/Fonts/arial.ttf"#  RESİMLERİN ANA YOLUDUR
LIMIT = 22 # ÇÖP LİMİTİ DIR 

son_tiklama_zamani = 0
tiklama_gecikmesi = 0.6 

# --- PARTİKÜL SİSTEMİ ---
class Partikul:
    def __init__(self, x, y, renk):
        self.x, self.y = x, y
        self.renk = renk
        self.vx, self.vy = random.uniform(-10, 10), random.uniform(-12, 5)
        self.omur = random.randint(20, 40)
        self.boyut = random.randint(4, 10)

    def guncelle(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.5  
        self.omur -= 1

    def ciz(self, img):
        if self.omur > 0:
            cv2.rectangle(img, (int(self.x), int(self.y)), 
                          (int(self.x + self.boyut), int(self.y + self.boyut)), self.renk, -1)

aktif_partikuller = []
bosalan_partikuller = [] 
bosalan_gorseller = [] 
# ---- PARTIKULLERİN REKLERİNİ AYARLARI ------
# ----- RENK KODLARI B G R DİR ::: B = MAVİ ::: G = YEŞİL :::: R = KIRMIZI DIR ------- 
PARTIKUL_RENKLERI = {
    "PLASTİK": (255, 0, 0), "CAM": (0, 255, 0), "KAĞIT": (200, 200, 200),
    "METAL": (100, 100, 100), "DİĞER": (0, 0, 255), "PİL": (0, 165, 255)
}

# --- KONUŞMA FOKSİYONU ---
def seslendir(metin):
    def cal():
        global konusuyor # Dışarıdaki ana değişkeni kontrol etmemi sağla
        if konusuyor: return # Eğer işlem zaten yapılıyorsa içeri girme ve dur
        konusuyor = True # İşlem başladığı için kapıyı kilitle ki başkası girmesin
        try:
            tts = gTTS(text=metin, lang='tr', slow=False) # gtts ile metini okutuyorum ve dili türkçe olarak ayarladım ve yavaş okumayı kapattım
            ses_dosyasi = "bildirim.mp3" # ses dosyasinin ismini bildirim koydum
            tts.save(ses_dosyasi)# ve bu dosyayı kaydettim
            playsound(ses_dosyasi)# ve bunu çaldım
            if os.path.exists(ses_dosyasi): os.remove(ses_dosyasi) # sonra bunu sildim ve bu sayede pc de yer kaplamıyor 
        except: pass
        konusuyor = False # kapıyı geri açar 
    threading.Thread(target=cal, daemon=True).start() # ve herşey den önce bu foksiyonu kur dedim
# ------ RESİM YÜKLEME FOKSİYONU ----- 
def resim_yukle(yol, boyut=(60, 60), alpha=False):
    try:
        mode = cv2.IMREAD_UNCHANGED if alpha else cv2.IMREAD_COLOR # Resmin şeffaf
        resim = cv2.imdecode(np.fromfile(yol, dtype=np.uint8), mode) # çalıştırmak için 
        if resim is None: raise ValueError # Eğer dosya bozuksa veya yol yanlışsa hata oluştur diyerek işlemi durdurur
        return cv2.resize(resim, boyut)# Resim başarıyla okunduysa istenen boyuta getirir
    except: 
        return None # eyer program çökerse boş döndür bu işlemde programın çökmesini engelliyor
# ------ÇÖPLERİ TEMİZLEME FOKSİYONU--------
def sistemi_bosalt():
    global sayaclar, geri_donusum_gorsel, dolum_zamanlari # Fonksiyonun dışındaki ana değişkenlere (sayaçlar, görseller ve zaman verileri) erişim sağlar.
    for k in sayaclar: sayaclar[k] = 0 # Tüm nesne sayar
    for k in geri_donusum_gorsel: geri_donusum_gorsel[k] = []#Hafızada tutulan tüm geri dönüşüm resim listelerini temizler
    dolum_zamanlari.clear()# Nesnelerin ne zaman atıldığına dair tutulan zaman kayıtlarını tamamen siler.
    seslendir("Sistem temizlendi") #stem boşaldı diye konuşur

# ----- ÇÖP RESİMLERİNİ YÜKLEME KODU-----
cop_kutusu_img = resim_yukle(ana_yol + "cop2.png", (180, 150), True)# çöp kutusunun resmini yükler
cop_gorselleri = { 
    "PLASTİK": resim_yukle(ana_yol + "plastik.png", (50, 50)),
    "CAM": resim_yukle(ana_yol + "cam.png", (50, 50)),
    "KAĞIT": resim_yukle(ana_yol + "kağıt.png", (50, 50)),
    "METAL": resim_yukle(ana_yol + "metal.png", (50, 50)),
    "DİĞER": resim_yukle(ana_yol + "diyer.png", (50, 50)), 
    "PİL": resim_yukle(ana_yol + "pil.png", (50, 50)),
}

# ------ BUTTON RESİMLERİNİ YÜKLEME KODU -------
temizle_ikon = resim_yukle(ana_yol + "temizle.png", (110, 50))# temizlik buttonnun resmini yükler
ayristir_ikon = resim_yukle(ana_yol + "ayristir.png", (110, 50))# ayristirma buttonnun resmini yükler
boz_ikon = resim_yukle(ana_yol + "boz.png", (110, 50))#bozma buttonnun resmini yükler

sayaclar = {k: 0 for k in cop_gorselleri.keys()} # hangi çöp türünden kaçtane olduğunu tutar 
geri_donusum_gorsel = {k: [] for k in cop_gorselleri.keys()}#Tespit edilen çöplerin resimlerini kategorilerine göre depolamak için her türe ait boş bir liste açar.
cop_isimleri = list(cop_gorselleri.keys())# Çöp türlerinin adlarını (anahtarlarını) bir liste haline getirerek daha sonra kolayca erişilmesini sağlar.

copler = [] # çöpler diye boş bir dizin oluşturu
for i in range(6): # 6 adet çöp nesnesi üretir
    tip = random.choice(cop_isimleri)# çöpü rasgele şeçer
    x_pos = random.choice([random.randint(30, 180), random.randint(460, 580)]) # Çöpün ekranın sağında mı yoksa solunda mı duracağını belirler (orta kısmı boş bırakmak için iki farklı aralıktan rastgele sayı seçer).
    copler.append({"id": i, "x": x_pos, "y": random.randint(-600, -100), "tip": tip, "tutuluyor": False, "vy": 0}) #Oluşturulan bu çöpü bir sözlük (dictionary) yapısı olarak listeye ekler. İçinde şunlar bulunur


mp_hands = mp.solutions.hands # Google’ın geliştirdiği MediaPipe kütüphanesinin "El Takip" modülünü sisteme dahil eder.
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7) # El tanıma motorunu şu iki özel ayarla başlatır Aynı anda sadece tek bir eli takip etmesini söyler Elin gerçekten el olduğundan emin olma eşiğidir (%70 hassasiyet). Bu, hata payını azaltır.
mp_draw = mp.solutions.drawing_utils#Tanınan elin üzerine eklemleri ve çizgileri çizebilmek için yardımcı çizim aracını hazırlar.
# ---- BU KODU CV2 DE KAMEREANINA ERİŞİR VE KAMERANIZI AÇTIĞI PENCEREYE ADINI VERİR -------
kamera = cv2.VideoCapture(0)# cv2 ile kamerayı açar
window_name = "Akilli Cop Kutusu" # ve kameraya Akilli Cop Kutusu adnı verir 
cv2.namedWindow(window_name)# ve çalıştırı
cv2.namedWindow("Geri Donusum Merkezi")

try:
    f30 = ImageFont.truetype(font_path, 30)# Yazıların boyutlarını ayarlar başlıklar için 30
    f20 = ImageFont.truetype(font_path, 20)# Yazıların boyutlarını ayarlar alt yazılar için 20  
except:
    f30 = f20 = ImageFont.load_default()
# Program ilk açıldığında kulanılan ses 
seslendir("Merhaba, hoş geldiniz! ")

# --- ANA DÖNGÜ ---
while True:
    ret, frame = kamera.read() # Kameradan bir kare görüntü alır.
    if not ret: break# Kamera kapanırsa programı durdurur.

    su_an = time.time()# Şu anki saati kontrol eder.
    for tip in cop_isimleri:# Her bir çöp kutusunu (plastik, cam vb.) tek tek gezer.
        if tip in dolum_zamanlari:# Eğer kutuda bekleyen bir çöp varsa;
            if su_an - dolum_zamanlari[tip] >= 10:# Kutu dolalı 10 saniye geçmiş mi diye bakar:
                # Kutunun ekrandaki yerini hesaplar:
                idx = cop_isimleri.index(tip)
                gx, gy = (idx % 3) * 300 + 150, (idx // 3) * 300 + 150
                renk = PARTIKUL_RENKLERI.get(tip, (255, 255, 255))
                # Renkli bir "boşaltma patlaması" (animasyon) oluşturur
                for _ in range(40): bosalan_partikuller.append(Partikul(gx, gy, renk))
                for g in geri_donusum_gorsel[tip]:
                    bosalan_gorseller.append({"img": g.copy(), "x": gx - 25, "y": gy, "vy": random.uniform(2, 6)})
                # Kutudaki çöpleri temizler (Sıfırlama):
                sayaclar[tip] = 0
                geri_donusum_gorsel[tip] = []
                del dolum_zamanlari[tip]

    frame = cv2.resize(frame, (640, 480))# Görüntü boyutunu 640x480 yaparak sistemi hızlandırır.
    frame = cv2.flip(frame, 1)# Görüntüyü ayna gibi ters çevirir (Sağ elimiz sağda görünsün diye).
    h, w, _ = frame.shape# Ekranın yükseklik ve genişlik değerlerini değişkene kaydeder.
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)# OpenCV'nin BGR renklerini, yapay zekanın sevdiği RGB'ye çevirir.
    sonuc = hands.process(rgb)# Hazırlanan bu görüntüyü yapay zekaya gönderip eli aratır.
# Eğer ekranda bir el varsa, elin iskeletini çizer ve işaret parmağının ucunu (8. nokta) bulup koordinatlarını gerçek piksel değerlerine çevirir.
    parmak_x, parmak_y = None, None
    if sonuc.multi_hand_landmarks:
        for el in sonuc.multi_hand_landmarks:
            mp_draw.draw_landmarks(frame, el, mp_hands.HAND_CONNECTIONS)
            parmak = el.landmark[8] # mentisten 8'i alır bu'da eldeki işaret parmana denk gelir 
            parmak_x, parmak_y = int(parmak.x * w), int(parmak.y * h)

    # --- BUTON ÇİZİMLERİ -----
    
    if temizle_ikon is not None:
        frame[10:60, 520:630] = temizle_ikon
    else:
        cv2.rectangle(frame, (520, 10), (630, 60), (200, 50, 50), -1)
        cv2.putText(frame, "Temizle", (540, 42), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 2)
    
    # --------- AYRIŞTIR / BOZ BUTONU KODU ---------
    if ayrisma_basladi:
        if boz_ikon is not None:
            frame[10:60, 400:510] = boz_ikon
        else:
            cv2.rectangle(frame, (400, 10), (510, 60), (0, 200, 0), -1)
            cv2.putText(frame, "BOZ", (415, 42), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 2)
    else:
        if ayristir_ikon is not None:
            frame[10:60, 400:510] = ayristir_ikon
        else:
            cv2.rectangle(frame, (400, 10), (510, 60), (0, 125, 200), -1)
            cv2.putText(frame, "Ayristir", (415, 42), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 2)
# -------- BU KOD Parmak Takibi Kontrolü ,Tıklama Gecikmesi ,Temizle Butonu VE Ayrıştır / Boz Butonu Algılama --------
    if parmak_x is not None and parmak_y is not None:
        if su_an - son_tiklama_zamani > tiklama_gecikmesi:
            if 520 < parmak_x < 630 and 10 < parmak_y < 60:
                sistemi_bosalt()
                son_tiklama_zamani = su_an
            elif 400 < parmak_x < 510 and 10 < parmak_y < 60:
                ayrisma_basladi = not ayrisma_basladi
                son_tiklama_zamani = su_an

    # ----- Çöp kutusu çizimi ----
    ry, rx = cop_kutusu_img.shape[:2]
    x_ofset, y_ofset = (w // 2) - (rx // 2), h - ry - 30
    if cop_kutusu_img.shape[2] == 4:
        mask = cop_kutusu_img[:, :, 3] / 255.0
        for c in range(3):
            frame[y_ofset:y_ofset + ry, x_ofset:x_ofset + rx, c] = \
                frame[y_ofset:y_ofset + ry, x_ofset:x_ofset + rx, c] * (1 - mask) + cop_kutusu_img[:, :, c] * mask

    # ---- ÇÖP ETKİLEŞİM VE FİZİK MOTORU: Çöplerin düşmesini, tutulmasını ve kutuya atılmasını yönetir ----
    for cop in copler:
        if not cop["tutuluyor"]:
            cop["vy"] += 1.2; cop["y"] += int(cop["vy"])
            if cop["y"] > h - 80: cop["y"], cop["vy"] = h - 80, 0
            if parmak_x is not None and tutulan_cop_id is None:
                if np.sqrt((parmak_x - cop["x"]) ** 2 + (parmak_y - cop["y"]) ** 2) < 55:
                    cop["tutuluyor"], tutulan_cop_id = True, cop["id"]
        else:
            if parmak_x is not None:
                cop["x"], cop["y"] = parmak_x, parmak_y
                if not konusuyor and x_ofset < cop["x"] < x_ofset + rx and y_ofset < cop["y"] < y_ofset + ry:
                    tip = cop["tip"]
                    if sayaclar[tip] < LIMIT:
                        for _ in range(15): aktif_partikuller.append(Partikul(cop["x"], cop["y"], PARTIKUL_RENKLERI.get(tip, (255,255,255))))
                        sayaclar[tip] += 1
                        geri_donusum_gorsel[tip].append(cop_gorselleri[tip].copy()) 
                        seslendir(f"Bu bir {tip.lower()}")
                        if sayaclar[tip] >= LIMIT:
                            dolum_zamanlari[tip] = time.time()
                            seslendir(f"{tip} kutusu doldu")
                        cop["x"] = random.choice([random.randint(30, 180), random.randint(460, 580)])
                        cop["y"], cop["vy"], cop["tutuluyor"], tutulan_cop_id = -150, 0, False, None
                    else:
                        seslendir(f"{tip} dolu")
                        cop["y"], cop["tutuluyor"], tutulan_cop_id = y_ofset - 150, False, None
            else: cop["tutuluyor"], tutulan_cop_id = False, None
        # --- GÖRSEL ÇİZİM VE EFEKT SİSTEMİ: Çöpleri, patlama efektlerini EKLER------
        gh, gw = cop_gorselleri[cop["tip"]].shape[:2]
        if 0 <= int(cop["y"]) < h - gh and 0 <= int(cop["x"]) < w - gw:
            frame[int(cop["y"]):int(cop["y"]) + gh, int(cop["x"]):int(cop["x"]) + gw] = cop_gorselleri[cop["tip"]]

    for p in aktif_partikuller[:]:
        p.guncelle(); p.ciz(frame)
        if p.omur <= 0: aktif_partikuller.remove(p)
#  ------ EKRANA BİR METİN EKLER  ------
    frame_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(frame_pil)
    draw.text((20, 20), "Lütfen çöpleri kutuya atın", font=f30, fill=(60, 5, 255))
    frame = cv2.cvtColor(np.array(frame_pil), cv2.COLOR_RGB2BGR)

    # --- GERİ DÖNÜŞÜM MERKEZİ GÖRSELLEŞTİRME: Çöplerin kutulara ayrıştırılmasını, dolum sürelerini ve boşaltma animasyonlarını yönetir ---
    geri_frame = np.zeros((600, 900, 3), dtype=np.uint8)
    # 1. Animasyonlar: Boşalan kutulardan fırlayan partikülleri ve düşen çöp görsellerini çiz
    for p in bosalan_partikuller[:]:
        p.guncelle(); p.ciz(geri_frame)
        if p.omur <= 0: bosalan_partikuller.remove(p)

    yeni_bosalan_gorseller = [] # Hata vermemesi için görselleri filtreleyerek aşağı düşür
    for b in bosalan_gorseller:
        b["y"] += b["vy"]; b["vy"] += 0.5
        gh, gw = b["img"].shape[:2]
        if b["y"] < 600:
            if 0 <= int(b["y"]) < 600 - gh and 0 <= int(b["x"]) < 900 - gw:
                geri_frame[int(b["y"]):int(b["y"])+gh, int(b["x"]):int(b["x"])+gw] = b["img"]
            yeni_bosalan_gorseller.append(b)
    bosalan_gorseller = yeni_bosalan_gorseller
# 2. Mod Kontrolü: Ayrıştırma başlamadıysa çöpleri karışık göster, başladıysa kategorilere ayır
    if not ayrisma_basladi:
        cv2.rectangle(geri_frame, (100, 50), (800, 550), (40, 40, 40), 2)
        ox, oy = 120, 70
        for tip in cop_isimleri:
            for g in geri_donusum_gorsel[tip]:
                gh, gw = g.shape[:2]
                if oy + gh < 550:
                    geri_frame[oy:oy+gh, ox:ox+gw] = g
                    ox += gw + 5
                    if ox > 770: ox = 120; oy += gh + 5
        geri_frame_son = geri_frame
    else:
        # --- AYRIŞTIRMA MODU: Ekranı 6 bölmeye ayır ve her çöpü kendi kutusuna yerleştir ---
        geri_pil = Image.fromarray(cv2.cvtColor(geri_frame, cv2.COLOR_BGR2RGB))
        draw_geri = ImageDraw.Draw(geri_pil)
        for i, tip in enumerate(cop_isimleri):
            x, y = (i % 3) * 300, (i // 3) * 300
            # Sayaçları ve boşalmaya kalan süreyi (geri sayım) yazdır
            yazi = f"{tip}: {sayaclar[tip]}"
            if tip in dolum_zamanlari:
                kalan = max(0, int(10 - (time.time() - dolum_zamanlari[tip])))
                yazi += f" ({kalan}s)"
            draw_geri.text((x + 20, y + 15), yazi, font=f20, fill=(255, 255, 255))
        geri_frame_son = cv2.cvtColor(np.array(geri_pil), cv2.COLOR_RGB2BGR)
        for i, tip in enumerate(cop_isimleri):
            x, y = (i % 3) * 300, (i // 3) * 300
            cv2.rectangle(geri_frame_son, (x, y), (x + 300, y + 300), (100, 100, 100), 1)
            gx, gy = x + 10, y + 50
            for g in geri_donusum_gorsel[tip]:
                gh, gw = g.shape[:2]
                if gy + gh < y + 300:
                    geri_frame_son[gy:gy + gh, gx:gx + gw] = g
                    gx += gw + 5
                    if gx + gw > x + 300: gx, gy = x + 10, gy + gh + 5
# ------ CV2 İMSHOW KODU İLE TÜM İŞLEMLERİ ÇALIŞTIRI ---------
    cv2.imshow("Geri Donusum Merkezi", geri_frame_son)
    cv2.imshow(window_name, frame)
    if cv2.waitKey(1) & 0xFF == ord("q"): break
# --- SİSTEM KAPANIŞI: Kamerayı serbest bırakır ve açılan tüm pencereleri kapatarak programı sonlandırır ---
kamera.release()
cv2.destroyAllWindows()
