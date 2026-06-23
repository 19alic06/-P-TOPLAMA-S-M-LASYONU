import cv2 
import mediapipe as mp
import random
import numpy as np
from playsound import playsound
from gtts import gTTS
import os
import threading
import time 
from PIL import ImageFont, ImageDraw, Image

konusuyor = False
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
# ----partalükül rengi--------
PARTIKUL_RENKLERI = {
    "PLASTİK": (255, 0, 0), "CAM": (0, 255, 0), "KAĞIT": (200, 200, 200),
    "METAL": (100, 100, 100), "DİYERÇÖPLER": (0, 0, 139), "PİL": (0, 165, 255)
}
# ---- kodun çöpunün zamanının dolu olup olmadına bakar
dolum_zamanlari = {}
#-------ses ekler konuşması için dir-----
def seslendir(metin):
    def cal():
        global konusuyor
        if konusuyor:
            return
        konusuyor = True
        try:
            tts = gTTS(text=metin, lang='tr', slow=False)
            ses_dosyasi = "bildirim.mp3" #bildirim diye dosya oluşturu
            tts.save(ses_dosyasi)#ses dosyasını kayıt eder
            playsound(ses_dosyasi)# ve çalar
            if os.path.exists(ses_dosyasi):
                os.remove(ses_dosyasi)
        except Exception as e:
            print("Ses hatası:", e)
        konusuyor = False

    threading.Thread(target=cal).start()
# -----çöplerin resmini yükler------
def resim_yukle(yol, boyut=(60, 60), alpha=False):
    try:
        if alpha:
            resim = cv2.imdecode(np.fromfile(yol, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
        else:
            resim = cv2.imdecode(np.fromfile(yol, dtype=np.uint8), cv2.IMREAD_COLOR)
        if resim is None:
            raise ValueError
        return cv2.resize(resim, boyut)
    except:
        return np.zeros((boyut[1], boyut[0], 3), dtype=np.uint8)
#resimlerein nerede tutulduğunu yazar yol olarak
ana_yol = r"C:\Users\alico\Desktop\kodlar\çöp\\"
cop_kutusu_img = resim_yukle(ana_yol + "cop2.png", (180, 150), True)
# resimleri yükler
cop_gorselleri = {
    "PLASTİK": resim_yukle(ana_yol + "plastik.png", (50, 50)),
    "CAM": resim_yukle(ana_yol + "cam.png", (50, 50)),
    "KAĞIT": resim_yukle(ana_yol + "kağıt.png", (50, 50)),
    "METAL": resim_yukle(ana_yol + "metal.png", (50, 50)),
    "DİYER": resim_yukle(ana_yol + "diyer.png", (50, 50)),
    "PİL": resim_yukle(ana_yol + "pil.png", (50, 50)),
}

sayaclar = {k: 0 for k in cop_gorselleri.keys()}
geri_donusum_gorsel = {k: [] for k in cop_gorselleri.keys()}
LIMIT = 5

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

kamera = cv2.VideoCapture(0)# cv2 ile kameraı açar
window_name = "Akilli Cop Kutusu"# açtığı ilk kameraya akıllı çöp kutusu adını koyar
cv2.namedWindow(window_name)
cv2.namedWindow("Geri Donusum Merkezi")# ikici ye ise geri donüşüm merkezi diye adını koyar

cop_isimleri = list(cop_gorselleri.keys())
tutulan_cop_id = None
copler = []

for i in range(6):
    tip = random.choice(cop_isimleri)
    x_pos = random.choice([random.randint(30, 180), random.randint(460, 580)])
    copler.append({
        "id": i, "x": x_pos, "y": random.randint(-600, -100),
        "tip": tip, "tutuluyor": False, "vy": 0  
    })

font_path = "C:/Windows/Fonts/arial.ttf"
# kamerayı döngüye alırkı hemen açıp kapatmasın biz kapatana kadar kendi kalsın diye
while True:
    ret, frame = kamera.read()
    if not ret: break

    su_an = time.time()
#-------- ÇÖPLERİN DOLUOLDP OLMADINA BAKAR OLUYSA EYER 2DK'LİK BİR ZAMAN KOYAR KODLAR VE PARTALÜKDE EKLEMEYİ BURADA YAPAR-----------
    for tip in cop_isimleri:
        if tip in dolum_zamanlari:
            if su_an - dolum_zamanlari[tip] >= 10:
                idx = cop_isimleri.index(tip)
                gx, gy = (idx % 3) * 300 + 150, (idx // 3) * 300 + 150
                renk = PARTIKUL_RENKLERI.get(tip, (255, 255, 255))
                
                for _ in range(40):
                    bosalan_partikuller.append(Partikul(gx, gy, renk))
                
               
                for g in geri_donusum_gorsel[tip]:
                    bosalan_gorseller.append({"img": g.copy(), "x": gx - 25, "y": gy, "vy": random.uniform(2, 6)})
                
                sayaclar[tip] = 0
                geri_donusum_gorsel[tip] = []
                del dolum_zamanlari[tip]
# KAMERANIN BOYUNU AYARLAR
    frame = cv2.resize(frame, (640, 480))
    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    sonuc = hands.process(rgb)

    parmak_x = None
    parmak_y = None

    
    if sonuc.multi_hand_landmarks:
        for el in sonuc.multi_hand_landmarks:  
            mp_draw.draw_landmarks(frame, el, mp_hands.HAND_CONNECTIONS)
            parmak = el.landmark[8]
            parmak_x = int(parmak.x * w)
            parmak_y = int(parmak.y * h)

    ry, rx = cop_kutusu_img.shape[:2]
    x_ofset = (w // 2) - (rx // 2)
    y_ofset = h - ry - 30

    if cop_kutusu_img.shape[2] == 4:
        b, g, r, a = cv2.split(cop_kutusu_img)
        mask = a / 255.0
        for c in range(3):
            frame[y_ofset:y_ofset + ry, x_ofset:x_ofset + rx, c] = (
                    frame[y_ofset:y_ofset + ry, x_ofset:x_ofset + rx, c] * (1 - mask) +
                    cop_kutusu_img[:, :, c] * mask
            )
# TUTUYORMU DİYE KONTUROL EDER
    for cop in copler:
        if not cop["tutuluyor"]:
            cop["vy"] += 1.2
            cop["y"] += int(cop["vy"])
            if cop["y"] > h - 80:
                cop["y"] = h - 80
                cop["vy"] = 0

            if parmak_x is not None and tutulan_cop_id is None:
                mesafe = np.sqrt((parmak_x - cop["x"]) ** 2 + (parmak_y - cop["y"]) ** 2)
                if mesafe < 55:
                    cop["tutuluyor"] = True
                    tutulan_cop_id = cop["id"]
        else:
            if parmak_x is not None:
                cop["x"], cop["y"] = parmak_x, parmak_y
                if not konusuyor and x_ofset < cop["x"] < x_ofset + rx and y_ofset < cop["y"] < y_ofset + ry:
                    tip = cop["tip"]
                    if sayaclar[tip] < LIMIT:
                        renk = PARTIKUL_RENKLERI.get(tip, (255, 255, 255))
                        for _ in range(15): aktif_partikuller.append(Partikul(cop["x"], cop["y"], renk))
                        
                        sayaclar[tip] += 1
                        geri_donusum_gorsel[tip].append(cop_gorselleri[tip].copy()) 
                        seslendir(f"Bu bir {tip.lower()}") # ÇÖPÜ ATINCA BU BİR DER VE ÇÖPÜN ADINI SÖYLER
                        # LİMİT DOLUNCA ÇÖP KUTUSUNU SIFIRLAR
                        if sayaclar[tip] >= LIMIT:
                            dolum_zamanlari[tip] = time.time()
                            seslendir(f"{tip} kutusu doldu")

                        cop["x"] = random.choice([random.randint(30, 180), random.randint(460, 580)])
                        cop["y"], cop["vy"], cop["tutuluyor"] = -150, 0, False
                        tutulan_cop_id = None
                    # EYER DOLU ÇÖPE BİR ŞEY ATMAYA ÇALIŞIRSA BU ÇÖPÜN ADI DOLU DER
                    else:
                        seslendir(f"{tip} dolu")
                        cop["y"], cop["tutuluyor"] = y_ofset - 150, False
                        tutulan_cop_id = None
            else:
                cop["tutuluyor"] = False
                tutulan_cop_id = None

        gorsel = cop_gorselleri[cop["tip"]]
        gh, gw = gorsel.shape[:2]
        if 0 <= int(cop["y"]) < h - gh and 0 <= int(cop["x"]) < w - gw:
            frame[int(cop["y"]):int(cop["y"]) + gh, int(cop["x"]):int(cop["x"]) + gw] = gorsel

    for p in aktif_partikuller[:]:
        p.guncelle()
        p.ciz(frame)
        if p.omur <= 0: aktif_partikuller.remove(p)

    frame_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(frame_pil)
    try:
        f30 = ImageFont.truetype(font_path, 30)
        f20 = ImageFont.truetype(font_path, 20)
    except:
        f30 = f20 = ImageFont.load_default()
    draw.text((20, 20), "Lütfen çöpleri kutuya atın", font=f30, fill=(60, 5, 255))# EKRANA YAZI YAZAR
    frame = cv2.cvtColor(np.array(frame_pil), cv2.COLOR_RGB2BGR)

    geri_frame = np.zeros((600, 900, 3), dtype=np.uint8)

    # PARTELÜKLERİ GÜNCELLER
    for p in bosalan_partikuller[:]:
        p.guncelle()
        p.ciz(geri_frame)
        if p.omur <= 0: bosalan_partikuller.remove(p)
#  ÇÖP BOŞALINCA RESMİNİ GÜNCELLER
    for b in bosalan_gorseller[:]:
        b["y"] += b["vy"]
        b["vy"] += 0.5
        gh, gw = b["img"].shape[:2]
        if b["y"] < 600:
            y_s, x_s = int(b["y"]), int(b["x"])
            if 0 <= y_s < 600 - gh and 0 <= x_s < 900 - gw:
                geri_frame[y_s:y_s+gh, x_s:x_s+gw] = b["img"]
        else:
            bosalan_gorseller.remove(b)

    geri_pil = Image.fromarray(cv2.cvtColor(geri_frame, cv2.COLOR_BGR2RGB))
    draw_geri = ImageDraw.Draw(geri_pil)
# ÇÖPLERİ OLUŞTURUR VE RASGELE EN FAZLA 6 ADAET KOYAR VE boşalma süresini yazar.
    for i, tip in enumerate(cop_isimleri):
        x, y = (i % 3) * 300, (i // 3) * 300
        cv2.rectangle(geri_frame, (x, y), (x + 300, y + 300), (255, 255, 255), 2)
        yazi = f"{tip}: {sayaclar[tip]}"
        if tip in dolum_zamanlari:
            kalan = max(0, int(120 - (time.time() - dolum_zamanlari[tip])))
            yazi += f" ({kalan}s)"
        draw_geri.text((x + 20, y + 15), yazi, font=f20, fill=(55, 25, 255))

    geri_frame_son = cv2.cvtColor(np.array(geri_pil), cv2.COLOR_RGB2BGR)
#   ÇÖP KUTUSUNUN ÜSTÜNDE ÇÖP OLÜŞMASINI ENGELLER
    for i, tip in enumerate(cop_isimleri):
        x, y = (i % 3) * 300, (i // 3) * 300
        gx, gy = x + 10, y + 50
        for g in geri_donusum_gorsel[tip]:
            gh, gw = g.shape[:2]
            if gy + gh < y + 300:
                geri_frame_son[gy:gy + gh, gx:gx + gw] = g
                gx += gw + 5
                if gx + gw > x + 300:
                    gx, gy = x + 10, gy + gh + 5
    # CV2 KODLARINI ÇALIŞTIRI
    cv2.imshow("Geri Donusum Merkezi", geri_frame_son)
    cv2.imshow(window_name, frame)
    # BU KODA  Q TUŞUNA BASINCA KAPATIR
    if cv2.waitKey(1) & 0xFF == ord("q"): break
# VE KODU DESTROY DER VE KOD BİTER 
kamera.release()
cv2.destroyAllWindows()
